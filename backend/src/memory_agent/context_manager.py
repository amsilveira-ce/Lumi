# context_manager.py - Centralized Context Manager (Single Source of Truth)
import logging
import uvicorn
import datetime
import json
import os
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Part,
    TextPart,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
    UnsupportedOperationError,
)
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_agent_text_message, new_task, completed_task, new_artifact
from a2a.utils.errors import ServerError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContextManager")


class ContextManager(AgentExecutor):
    """
    SINGLE SOURCE OF TRUTH for all conversational context.

    THREE-LAYER ARCHITECTURE:
    1. Conversation Context: Last 10 turns with timestamps
    2. Active Topic Context: Primary/secondary topics with confidence
    3. User Context: Profile, preferences, current state

    CRITICAL RULE:
    NO AGENT may be invoked without first retrieving context from here.
    """

    # {user_id: context_data}
    context_store = {}

    def _get_empty_context(self, user_id: str) -> dict:
        """
        Creates an empty context structure for a new user.
        """
        return {
            "user_id": user_id,

            # LAYER 1: Conversation Context
            "conversation_history": [],  # Last 10 turns: [{"role": "user|assistant", "content": "...", "timestamp": "..."}]

            # LAYER 2: Active Topic Context
            "active_topics": {
                "primary": None,  # {"topic": "loneliness", "confidence": 0.9, "started_at": "...", "keywords": [...]}
                "secondary": []   # [{"topic": "medication", "confidence": 0.6, "started_at": "..."}]
            },

            # LAYER 3: User Context
            "user_profile": {
                "age": None,
                "is_elder": True,
                "conditions": [],  # ["heart arrhythmia", "diabetes"]
                "emergency_contacts": [],
                "preferences": {
                    "tone": "warm",  # warm, formal, casual
                    "pace": "slow",  # slow, medium, fast
                    "cognitive_comfort": "intermediate"  # beginner, intermediate, advanced
                }
            },

            "current_state": {
                "emotional_state": "neutral",  # neutral, distressed, calm, anxious, sad, happy
                "safety_status": "safe",  # safe, monitoring, emergency
                "cognitive_clarity": "clear",  # clear, confused, disoriented
                "engagement_level": "active",  # active, passive, withdrawn
                "last_updated": datetime.datetime.now().isoformat()
            },

            # Metadata
            "metadata": {
                "session_start": datetime.datetime.now().isoformat(),
                "total_turns": 0,
                "last_interaction": None
            }
        }

    def _detect_topics(self, user_message: str, assistant_message: str = "") -> list:
        """
        Detects topics from conversation using keyword matching.
        Returns list of (topic, confidence) tuples.

        In production, replace with LLM-based topic extraction.
        """
        topics = []
        text = (user_message + " " + assistant_message).lower()

        # Topic keyword mapping
        topic_keywords = {
            "loneliness": ["lonely", "alone", "nobody", "isolated", "miss", "visits"],
            "health_concern": ["pain", "hurt", "sick", "dizzy", "headache", "feel bad"],
            "medication": ["medication", "pill", "medicine", "prescription", "dose"],
            "family": ["son", "daughter", "family", "grandson", "granddaughter", "relatives"],
            "emergency": ["fall", "fell", "help", "emergency", "urgent", "911"],
            "contact_request": ["call", "contact", "phone", "reach", "speak to", "talk to"],
            "confusion": ["forgot", "remember", "confused", "lost", "where am i"],
            "mood": ["sad", "happy", "anxious", "worried", "scared", "excited"],
            "activities": ["bored", "do something", "activity", "nothing to do"],
            "schedule": ["appointment", "reminder", "doctor", "schedule", "calendar"]
        }

        for topic, keywords in topic_keywords.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                confidence = min(1.0, matches / len(keywords) * 2)  # Scale confidence
                topics.append((topic, confidence))

        # Sort by confidence
        topics.sort(key=lambda x: x[1], reverse=True)
        return topics[:3]  # Top 3 topics

    def _update_topics(self, context: dict, user_message: str, assistant_message: str = ""):
        """
        Updates active topics based on the latest conversation turn.
        """
        detected_topics = self._detect_topics(user_message, assistant_message)

        if not detected_topics:
            return  # No topic change

        # Update primary topic
        new_primary = detected_topics[0]
        current_primary = context["active_topics"]["primary"]

        if current_primary is None or new_primary[1] > current_primary.get("confidence", 0):
            context["active_topics"]["primary"] = {
                "topic": new_primary[0],
                "confidence": new_primary[1],
                "started_at": datetime.datetime.now().isoformat(),
                "keywords": []  # Can be populated from user message
            }
            logger.info(f"🎯 [TOPIC] Primary topic updated: {new_primary[0]} (confidence: {new_primary[1]:.2f})")

        # Update secondary topics
        context["active_topics"]["secondary"] = [
            {
                "topic": topic,
                "confidence": conf,
                "started_at": datetime.datetime.now().isoformat()
            }
            for topic, conf in detected_topics[1:3]  # Up to 2 secondary topics
        ]

    def _update_state(self, context: dict, risk_assessment: dict = None):
        """
        Updates user's current state based on risk assessment or conversation patterns.
        """
        if risk_assessment:
            # Map risk level to emotional/safety state
            risk_level = risk_assessment.get("risk_level", "SAFE")
            risk_category = risk_assessment.get("risk_category", "unknown")

            if risk_level == "HIGH":
                context["current_state"]["safety_status"] = "emergency"
                context["current_state"]["emotional_state"] = "distressed"
            elif risk_level == "MEDIUM":
                context["current_state"]["safety_status"] = "monitoring"
                if risk_category == "emotional":
                    context["current_state"]["emotional_state"] = "anxious"  # or "sad" based on specifics
                elif risk_category == "medical":
                    context["current_state"]["cognitive_clarity"] = "confused"
            else:
                context["current_state"]["safety_status"] = "safe"

        context["current_state"]["last_updated"] = datetime.datetime.now().isoformat()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Handles context operations:
        - get_context: Retrieve full context package
        - update_turn: Add new conversation turn
        - update_state: Update user state
        - get_history: Get conversation history only
        """
        try:
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            user_input = context.get_user_input()
            logger.info(f"📨 [CONTEXT_MGR] Received: {user_input[:100]}...")

            # Process context request
            response_text = await self.process_context_request(user_input)

            logger.info(f"📤 [CONTEXT_MGR] Response length: {len(response_text)} chars")

            completed = completed_task(
                task.id,
                task.context_id,
                [new_artifact([Part(root=TextPart(text=response_text))], "context_result")],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"❌ [CONTEXT_MGR] Error: {e}", exc_info=True)
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Context operation failed: {str(e)}",
                    context.context_id,
                    context.task_id,
                ),
                final=True,
            )

    async def process_context_request(self, text: str) -> str:
        """
        Processes context management operations.

        Actions:
        - get_context: Returns full context package
        - update_turn: Adds new conversation turn and updates topics
        - update_state: Updates user's current state
        - get_history: Returns conversation history only
        """
        try:
            data = json.loads(text)
            action = data.get("action")
            user_id = data.get("user_id", "default")

            # Initialize context if needed
            if user_id not in self.context_store:
                self.context_store[user_id] = self._get_empty_context(user_id)
                logger.info(f"🆕 [CONTEXT_MGR] Initialized context for user: {user_id}")

            ctx = self.context_store[user_id]

            if action == "get_context":
                # Return full context package
                logger.info(f"📦 [CONTEXT_MGR] Fetching full context for {user_id}")
                return json.dumps(ctx)

            elif action == "update_turn":
                # Add new conversation turn
                user_message = data.get("user_message", "")
                assistant_message = data.get("assistant_message", "")
                risk_assessment = data.get("risk_assessment")  # Optional

                turn = {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                ctx["conversation_history"].append(turn)

                if assistant_message:
                    turn = {
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    ctx["conversation_history"].append(turn)

                # Keep only last 10 turns
                ctx["conversation_history"] = ctx["conversation_history"][-10:]

                # Update topics
                self._update_topics(ctx, user_message, assistant_message)

                # Update state if risk assessment provided
                if risk_assessment:
                    self._update_state(ctx, risk_assessment)

                # Update metadata
                ctx["metadata"]["total_turns"] += 1
                ctx["metadata"]["last_interaction"] = datetime.datetime.now().isoformat()

                logger.info(f"✅ [CONTEXT_MGR] Updated context for {user_id} (total turns: {ctx['metadata']['total_turns']})")

                return json.dumps({"status": "success", "turns": ctx["metadata"]["total_turns"]})

            elif action == "update_state":
                # Update user state
                emotional_state = data.get("emotional_state")
                safety_status = data.get("safety_status")
                cognitive_clarity = data.get("cognitive_clarity")

                if emotional_state:
                    ctx["current_state"]["emotional_state"] = emotional_state
                if safety_status:
                    ctx["current_state"]["safety_status"] = safety_status
                if cognitive_clarity:
                    ctx["current_state"]["cognitive_clarity"] = cognitive_clarity

                ctx["current_state"]["last_updated"] = datetime.datetime.now().isoformat()

                logger.info(f"🔄 [CONTEXT_MGR] State updated for {user_id}: {ctx['current_state']}")

                return json.dumps({"status": "success", "state": ctx["current_state"]})

            elif action == "get_history":
                # Return conversation history only
                logger.info(f"📜 [CONTEXT_MGR] Fetching history for {user_id} ({len(ctx['conversation_history'])} turns)")
                return json.dumps(ctx["conversation_history"])

            elif action == "update_profile":
                # Update user profile
                profile_data = data.get("profile", {})
                ctx["user_profile"].update(profile_data)
                logger.info(f"👤 [CONTEXT_MGR] Profile updated for {user_id}")
                return json.dumps({"status": "success", "profile": ctx["user_profile"]})

            else:
                return json.dumps({"error": f"Unknown action: {action}"})

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in context request: {text}")
            return json.dumps({"error": "Invalid context request format"})
        except Exception as e:
            logger.error(f"Context processing error: {e}", exc_info=True)
            return json.dumps({"error": f"Context error: {str(e)}"})

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())


def get_agent_card(host: str = "0.0.0.0", port: int = 8083) -> AgentCard:
    """Defines the capabilities of the Context Manager."""
    return AgentCard(
        name="Context Manager",
        description=(
            "Centralized context management system - SINGLE SOURCE OF TRUTH for GrandCompanion. "
            "Maintains conversation history, active topics, user profile, and current state. "
            "ALL agents must retrieve context from here before processing."
        ),
        url=f"http://{host}:{port}/",
        version="2.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"], output_modes=["text"], streaming=False
        ),
        skills=[
            AgentSkill(
                id="get_context",
                name="Get Full Context Package",
                description="Returns complete context: conversation history, active topics, user profile, current state.",
                examples=["Get context for routing decision", "Fetch user state before safety check"],
                tags=["context", "orchestration", "coordination"],
            ),
            AgentSkill(
                id="update_turn",
                name="Update Conversation Turn",
                description="Adds new turn to history, updates topics, refreshes state.",
                examples=["Record user message and agent response", "Update conversation flow"],
                tags=["conversation", "tracking", "continuity"],
            ),
            AgentSkill(
                id="update_state",
                name="Update User State",
                description="Updates user's emotional/safety/cognitive state based on agent assessments.",
                examples=["Mark user as distressed", "Set safety status to emergency"],
                tags=["state-management", "safety", "monitoring"],
            ),
            AgentSkill(
                id="get_history",
                name="Get Conversation History",
                description="Returns last 10 turns for context-aware responses.",
                examples=["Fetch recent conversation for LLM prompt", "Review interaction history"],
                tags=["history", "memory", "retrieval"],
            ),
        ],
    )


def main():
    """Starts the Context Manager Server on port 8083."""
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8083))

    logger.info(f"🚀 Starting Context Manager (Single Source of Truth) on {host}:{port}")

    agent_card = get_agent_card(host, port)
    task_store = InMemoryTaskStore()
    agent_executor = ContextManager()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=task_store
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    app = server.build()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
