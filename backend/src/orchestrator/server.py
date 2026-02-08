# orchestrator_server.py - Main entry point for GrandCompanion Dashboard
import logging
import uvicorn
import json
import os
import asyncio
import httpx
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
from a2a.client import A2ACardResolver, ClientFactory, create_text_message_object
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrchestratorServer")


# ==========================================
# Helper: A2A Agent Caller
# ==========================================
async def call_a2a_agent(agent_url: str, message_text: str) -> dict:
    """
    Helper to send a message to an A2A agent and return the response.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            card_resolver = A2ACardResolver(httpx_client, agent_url)
            agent_card = await card_resolver.get_agent_card()

            config = ClientConfig(
                httpx_client=httpx_client, supported_transports=[TransportProtocol.jsonrpc]
            )
            factory = ClientFactory(config)
            client = factory.create(agent_card)

            message = create_text_message_object(content=message_text)
            final_response = None
            async for response_chunk in client.send_message(message):
                final_response = response_chunk

            if not final_response:
                return {"status": "error", "error": "No response from agent"}

            # Extract text from response
            # The A2A client returns different formats depending on the transport
            response_text = ""

            # If it's a tuple (common with some A2A transports)
            if isinstance(final_response, tuple) and len(final_response) > 0:
                # Usually the first element contains the message/content
                response_obj = final_response[0] if len(final_response) > 0 else None
                if response_obj and hasattr(response_obj, "artifacts"):
                    for artifact in response_obj.artifacts:
                        if hasattr(artifact, "parts"):
                            for part in artifact.parts:
                                if hasattr(part, "root") and hasattr(part.root, "text"):
                                    response_text += part.root.text
                                elif hasattr(part, "text"):
                                    response_text += part.text
            # If it's an object with artifacts
            elif hasattr(final_response, "artifacts") and final_response.artifacts:
                for artifact in final_response.artifacts:
                    if hasattr(artifact, "parts"):
                        for part in artifact.parts:
                            if hasattr(part, "root") and hasattr(part.root, "text"):
                                response_text += part.root.text
                            elif hasattr(part, "text"):
                                response_text += part.text
            # Fallback: check for parts directly
            elif hasattr(final_response, "parts"):
                for part in final_response.parts:
                    if hasattr(part, "root") and hasattr(part.root, "text"):
                        response_text += part.root.text
                    elif hasattr(part, "text"):
                        response_text += part.text

            return {"status": "success", "response_text": response_text}
    except Exception as e:
        logger.error(f"A2A call to {agent_url} failed: {e}")
        return {"status": "error", "error": str(e)}


# ==========================================
# Orchestrator Executor
# ==========================================
class OrchestratorExecutor(AgentExecutor):
    """
    Main orchestrator that routes user messages to appropriate agents.
    Handles:
    1. Safety checks (always first)
    2. Memory retrieval and storage
    3. Conversation generation
    4. UI widget commands
    """

    # Agent URLs (configurable via environment variables)
    SAFETY_AGENT_URL = os.environ.get("SAFETY_AGENT_URL", "http://localhost:8080")
    CONVERSATION_AGENT_URL = os.environ.get(
        "CONVERSATION_AGENT_URL", "http://localhost:8081"
    )
    MEMORY_AGENT_URL = os.environ.get("MEMORY_AGENT_URL", "http://localhost:8083")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Main execution flow:
        1. Parse user input
        2. Check safety (always)
        3. Route to appropriate handler
        4. Return response with UI commands
        """
        try:
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            user_input = context.get_user_input()
            logger.info(f"📨 [ORCHESTRATOR] Received: {user_input}")

            # Parse request
            try:
                request_data = json.loads(user_input)
                action = request_data.get("action", "conversation")

                # Check if data is nested under 'data' key (from Dashboard)
                if "data" in request_data:
                    data_obj = request_data["data"]
                    message = data_obj.get("message", "")
                    user_id = data_obj.get("user_id", "default_user")
                    elder_profile = data_obj.get("elder_profile", {})
                else:
                    # Direct format
                    message = request_data.get("message", "")
                    user_id = request_data.get("user_id", "default_user")
                    elder_profile = request_data.get("elder_profile", {})
            except json.JSONDecodeError:
                # Fallback: treat as plain text message
                action = "conversation"
                message = user_input
                user_id = "default_user"
                elder_profile = {}

            # ════════════════════════════════════════════════════════════
            # STEP 1: FETCH FULL CONTEXT (CRITICAL: Before ANY agent!)
            # ════════════════════════════════════════════════════════════
            logger.info(f"📦 [ORCHESTRATOR] Fetching full context for {user_id}")
            context_payload = json.dumps({
                "action": "get_context",
                "user_id": user_id
            })

            context_result = await call_a2a_agent(self.MEMORY_AGENT_URL, context_payload)

            try:
                full_context = json.loads(context_result.get("response_text", "{}"))
                if full_context is None:
                    full_context = {}
                logger.info(f"✅ [ORCHESTRATOR] Got context: {full_context.get('metadata', {}).get('total_turns', 0)} turns")
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                logger.warning(f"⚠️ [ORCHESTRATOR] Failed to parse context: {e}, using empty")
                full_context = {}

            # ════════════════════════════════════════════════════════════
            # STEP 2: CHECK SAFETY (with full context)
            # ════════════════════════════════════════════════════════════
            logger.info(f"🛡️ [ORCHESTRATOR] Checking safety for: {message}")
            safety_result = await self.check_safety(message, user_id, full_context)

            # ════════════════════════════════════════════════════════════
            # STEP 3: ROUTE (all agents receive context)
            # ════════════════════════════════════════════════════════════
            if not safety_result.get("is_safe", True):
                # HIGH RISK: Handle emergency
                response = await self.handle_emergency(
                    user_id, message, safety_result, elder_profile, full_context
                )
            else:
                # SAFE: Route to conversation agent
                if action == "conversation":
                    response = await self.handle_conversation(
                        user_id, message, elder_profile
                    )
                elif action == "ui_feedback":
                    response = await self.handle_ui_feedback(request_data)
                else:
                    response = {
                        "text": "I'm not sure how to help with that.",
                        "ui_commands": [],
                    }

            # STEP 3: Send response
            response_json = json.dumps(response)
            logger.info(f"📤 [ORCHESTRATOR] Sending: {response_json}")

            completed = completed_task(
                task.id,
                task.context_id,
                [new_artifact([Part(root=TextPart(text=response_json))], "response")],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"❌ [ORCHESTRATOR] Error: {e}", exc_info=True)
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Orchestrator failed: {str(e)}",
                    context.context_id,
                    context.task_id,
                ),
                final=True,
            )

    async def check_safety(self, message: str, user_id: str = "default", full_context: dict = None) -> dict:
        """
        Calls the Safety Agent to analyze the message WITH FULL CONTEXT.

        CRITICAL: Safety Agent needs context to detect patterns (e.g., repeated distress).

        Returns: {"is_safe": bool, "reason": str, "response_suggestion": str, "risk_level": str}
        """
        # Build context-aware safety payload
        safety_payload = {
            "message": message,
            "user_id": user_id
        }

        # Include context if available
        if full_context:
            safety_payload["conversation_history"] = full_context.get("conversation_history", [])[-5:]
            safety_payload["current_state"] = full_context.get("current_state", {})
            safety_payload["active_topics"] = full_context.get("active_topics", {})

        result = await call_a2a_agent(self.SAFETY_AGENT_URL, json.dumps(safety_payload))

        if result["status"] == "error":
            logger.warning(f"Safety check failed: {result['error']}")
            return {"is_safe": True, "reason": "Safety agent unavailable", "risk_level": "UNKNOWN"}

        try:
            safety_data = json.loads(result["response_text"])
            return safety_data
        except json.JSONDecodeError:
            # If safety agent returns non-JSON, assume safe
            return {"is_safe": True, "reason": "Unable to parse safety response", "risk_level": "SAFE"}

    async def handle_emergency(
        self, user_id: str, message: str, safety_result: dict, elder_profile: dict, full_context: dict = None
    ) -> dict:
        """
        Handles emergency situations WITH CONTEXT.

        Uses context to provide better emergency response (e.g., recent conversation, user state).

        Returns a response with emergency UI commands.
        """
        logger.warning(f"🚨 [ORCHESTRATOR] EMERGENCY DETECTED: {safety_result}")

        # Get emergency contacts (prioritize context over elder_profile)
        emergency_contacts = []
        if full_context:
            emergency_contacts = full_context.get("user_profile", {}).get("emergency_contacts", [])

        if not emergency_contacts:
            emergency_contacts = elder_profile.get("emergency_contacts", [])

        response_text = safety_result.get(
            "response_suggestion",
            "I'm concerned about what you said. I'm notifying your emergency contact immediately.",
        )

        # Update context with emergency turn and risk assessment
        asyncio.create_task(self.update_context_turn(
            user_id,
            message,
            response_text,
            risk_assessment={
                "risk_level": safety_result.get("risk_level", "HIGH"),
                "risk_category": safety_result.get("reason", "emergency"),
                "timestamp": safety_result.get("timestamp", "")
            }
        ))

        return {
            "text": response_text,
            "ui_commands": [
                {
                    "action": "show",
                    "component": "EmergencyAlert",
                    "props": {
                        "severity": "high",
                        "reason": safety_result.get("reason", "Crisis detected"),
                        "contacts": emergency_contacts[:1],  # Primary contact
                        "auto_call": True,
                    },
                }
            ],
            "is_emergency": True,
        }

    async def handle_conversation(
        self, user_id: str, message: str, elder_profile: dict
    ) -> dict:
        """
        Handles normal conversation flow with CENTRALIZED CONTEXT:

        CRITICAL RULE: No agent invoked without full context package!

        1. Fetch full context from Memory Agent (Single Source of Truth)
        2. Pass context to Conversation Agent
        3. Determine widgets based on message + active topics
        4. Update context with new turn
        """
        logger.info(f"💬 [ORCHESTRATOR] Handling conversation")

        # Ensure elder_profile is a dict (not None)
        if elder_profile is None:
            elder_profile = {}

        # ════════════════════════════════════════════════════════════
        # STEP 1: FETCH FULL CONTEXT (Single Source of Truth)
        # ════════════════════════════════════════════════════════════
        logger.info(f"📦 [ORCHESTRATOR] Fetching full context for {user_id}")
        context_payload = json.dumps({
            "action": "get_context",
            "user_id": user_id
        })

        context_result = await call_a2a_agent(self.MEMORY_AGENT_URL, context_payload)

        try:
            full_context = json.loads(context_result.get("response_text", "{}"))
            if full_context is None:
                full_context = {}
            # Safe extraction of primary topic
            primary = full_context.get('active_topics', {}).get('primary') if isinstance(full_context.get('active_topics'), dict) else None
            primary_topic_name = primary.get('topic', 'none') if primary else 'none'
            logger.info(f"✅ [ORCHESTRATOR] Got context: {full_context.get('metadata', {}).get('total_turns', 0)} turns, "
                       f"primary topic: {primary_topic_name}")
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning(f"⚠️ [ORCHESTRATOR] Failed to parse context: {e}, using empty")
            full_context = {}

        # ════════════════════════════════════════════════════════════
        # STEP 2: GENERATE RESPONSE (with full context)
        # ════════════════════════════════════════════════════════════

        # Format conversation history for agent
        conversation_history = full_context.get("conversation_history", [])
        history_text = "\n".join([
            f"{turn['role'].capitalize()}: {turn['content']}"
            for turn in conversation_history[-5:]  # Last 5 turns
        ])

        # Extract active topics for context
        active_topics = full_context.get("active_topics", {})
        primary_topic = active_topics.get("primary", {})
        topic_context = ""
        if primary_topic:
            topic_context = f"Current topic: {primary_topic.get('topic', 'general')} (confidence: {primary_topic.get('confidence', 0):.2f})"

        # Extract user state
        current_state = full_context.get("current_state", {})
        state_context = f"User state: {current_state.get('emotional_state', 'neutral')}, {current_state.get('cognitive_clarity', 'clear')}"

        conversation_payload = json.dumps(
            {
                "user_text": message,
                "memory_context": history_text,
                "topic_context": topic_context,
                "state_context": state_context,
                "mood": elder_profile.get("tone_preference", "casual"),
                "full_context": full_context  # Pass entire context for advanced usage
            }
        )

        conv_result = await call_a2a_agent(
            self.CONVERSATION_AGENT_URL, conversation_payload
        )
        response_text = conv_result.get(
            "response_text", "I'm here with you. Tell me more."
        )

        # ════════════════════════════════════════════════════════════
        # STEP 3: DETERMINE WIDGETS (using message + context)
        # ════════════════════════════════════════════════════════════
        ui_commands = self.determine_widgets(message, full_context)

        # ════════════════════════════════════════════════════════════
        # STEP 4: UPDATE CONTEXT with new turn
        # ════════════════════════════════════════════════════════════
        asyncio.create_task(self.update_context_turn(user_id, message, response_text))

        return {"text": response_text, "ui_commands": ui_commands}

    async def update_context_turn(
        self, user_id: str, user_message: str, assistant_message: str, risk_assessment: dict = None
    ):
        """
        Updates context with new conversation turn.

        This replaces the old save_memory method and uses the new
        Context Manager's update_turn action.
        """
        update_payload = json.dumps({
            "action": "update_turn",
            "user_id": user_id,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "risk_assessment": risk_assessment  # Optional: from Safety Agent
        })

        await call_a2a_agent(self.MEMORY_AGENT_URL, update_payload)
        logger.info(f"💾 [ORCHESTRATOR] Updated context turn for user {user_id}")

    async def get_memory_context(self, user_id: str, query: str) -> str:
        """
        LEGACY METHOD (for backward compatibility).

        Retrieves relevant memories from Memory Agent.
        Now uses get_history under the hood.
        """
        memory_payload = json.dumps(
            {"action": "retrieve", "user_id": user_id, "query": query}
        )
        result = await call_a2a_agent(self.MEMORY_AGENT_URL, memory_payload)
        return result.get("response_text", "")

    async def save_memory(self, user_id: str, user_message: str, bot_response: str):
        """
        LEGACY METHOD (for backward compatibility).

        Saves conversation to Memory Agent.
        Now uses update_turn under the hood.
        """
        memory_data = f"User: {user_message}\nAssistant: {bot_response}"
        memory_payload = json.dumps(
            {"action": "store", "user_id": user_id, "data": memory_data}
        )
        await call_a2a_agent(self.MEMORY_AGENT_URL, memory_payload)
        logger.info(f"💾 [ORCHESTRATOR] Saved memory for user {user_id} (legacy method)")

    def determine_widgets(self, message: str, full_context: dict = None) -> list:
        """
        Analyzes message to determine which UI widgets to show.

        Uses:
        - Message keywords
        - Active topics from context (if available)
        - User state from context (if available)

        This enables context-aware widget selection!
        """
        message_lower = message.lower()
        commands = []

        # Extract context information if available
        active_topics = {}
        current_state = {}
        if full_context:
            active_topics = full_context.get("active_topics", {})
            current_state = full_context.get("current_state", {})

        # Mood-related keywords
        mood_keywords = [
            "feel",
            "sad",
            "happy",
            "anxious",
            "lonely",
            "worried",
            "scared",
            "excited",
            "tired",
        ]
        if any(word in message_lower for word in mood_keywords):
            commands.append(
                {
                    "action": "show",
                    "component": "MoodSelector",
                    "props": {"widget_id": f"mood_{int(asyncio.get_event_loop().time())}"},
                }
            )

        # Activity-related keywords
        activity_keywords = ["bored", "do", "activity", "something", "nothing", "idle"]
        if any(word in message_lower for word in activity_keywords):
            commands.append(
                {
                    "action": "show",
                    "component": "ActivitySuggestions",
                    "props": {
                        "widget_id": f"activity_{int(asyncio.get_event_loop().time())}"
                    },
                }
            )

        # Reminder-related keywords
        reminder_keywords = [
            "remind",
            "medication",
            "pill",
            "doctor",
            "appointment",
            "schedule",
            "task",
        ]
        if any(word in message_lower for word in reminder_keywords):
            commands.append(
                {
                    "action": "show",
                    "component": "ReminderList",
                    "props": {
                        "widget_id": f"reminder_{int(asyncio.get_event_loop().time())}"
                    },
                }
            )

        # Contact/Call-related keywords
        contact_keywords = ["call", "contact", "phone", "talk to", "reach", "speak to", "get in touch"]
        person_keywords = ["son", "daughter", "family", "doctor", "friend", "grandson", "granddaughter", "caregiver", "someone"]

        # Check if user wants to contact someone
        has_contact_intent = any(word in message_lower for word in contact_keywords)
        mentions_person = any(word in message_lower for word in person_keywords)

        if has_contact_intent or (mentions_person and ("need" in message_lower or "want" in message_lower)):
            # Extract who they want to contact (basic pattern matching)
            contact_target = "someone"
            for person in person_keywords:
                if person in message_lower:
                    contact_target = person
                    break

            commands.append(
                {
                    "action": "show",
                    "component": "ContactSelector",
                    "props": {
                        "widget_id": f"contact_{int(asyncio.get_event_loop().time())}",
                        "requested_contact": contact_target,
                        "message": message  # Pass original message for context
                    },
                }
            )

        return commands

    async def handle_ui_feedback(self, request_data: dict) -> dict:
        """
        Handles UI feedback requests (e.g., "text is too small").
        """
        feedback = request_data.get("feedback", "")
        logger.info(f"🎨 [ORCHESTRATOR] UI Feedback: {feedback}")

        # Simple keyword-based UI adjustments
        ui_settings = {}
        feedback_lower = feedback.lower()

        if "small" in feedback_lower or "bigger" in feedback_lower:
            ui_settings["fontSize"] = "extra-large"
        elif "large" in feedback_lower or "smaller" in feedback_lower:
            ui_settings["fontSize"] = "normal"

        if "contrast" in feedback_lower or "see" in feedback_lower:
            ui_settings["contrast"] = "high"

        return {
            "text": "I've adjusted the display for you. Is this better?",
            "ui_commands": [
                {"action": "update_ui_settings", "component": "App", "props": ui_settings}
            ],
        }

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())


# ==========================================
# Agent Card Definition
# ==========================================
def get_agent_card(host: str = "0.0.0.0", port: int = 8082) -> AgentCard:
    """
    Defines the capabilities of the Orchestrator for the A2A network.
    """
    return AgentCard(
        name="GrandCompanion Orchestrator",
        description=(
            "Main orchestrator for the GrandCompanion elder care system. "
            "Routes user messages to Safety, Conversation, and Memory agents. "
            "Manages UI widget commands and emergency protocols."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"], output_modes=["text"], streaming=False
        ),
        skills=[
            AgentSkill(
                id="route_conversation",
                name="Route Conversation",
                description=(
                    "Routes user messages to appropriate specialist agents "
                    "(Safety, Conversation, Memory) based on content analysis."
                ),
                examples=[
                    "User sends a casual message",
                    "User expresses concern or distress",
                    "User asks about past conversations",
                ],
                tags=["routing", "orchestration", "message-handling"],
            ),
            AgentSkill(
                id="safety_monitoring",
                name="Safety Monitoring",
                description=(
                    "Continuously monitors all messages for safety concerns. "
                    "Immediately escalates to Safety Agent when crisis keywords detected."
                ),
                examples=[
                    "User mentions falling",
                    "User reports chest pain",
                    "User expresses severe distress",
                ],
                tags=["safety", "crisis-detection", "monitoring"],
            ),
            AgentSkill(
                id="widget_management",
                name="UI Widget Management",
                description=(
                    "Analyzes conversation context to determine which UI widgets "
                    "should be displayed (MoodSelector, ActivitySuggestions, ReminderList)."
                ),
                examples=[
                    "User mentions feeling sad → show MoodSelector",
                    "User says they're bored → show ActivitySuggestions",
                    "User mentions medication → show ReminderList",
                ],
                tags=["ui-control", "context-aware", "widget-commands"],
            ),
            AgentSkill(
                id="memory_coordination",
                name="Memory Coordination",
                description=(
                    "Coordinates with Memory Agent to retrieve relevant context "
                    "and store new conversation data."
                ),
                examples=[
                    "Retrieve user's family information",
                    "Store new preference or event",
                ],
                tags=["memory", "personalization", "context"],
            ),
        ],
    )


# ==========================================
# Main Entry Point
# ==========================================
def main():
    """
    Starts the Orchestrator Server on port 8082.
    This is the main entry point that the React Dashboard connects to.
    """
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8082))

    logger.info(f"🚀 Starting GrandCompanion Orchestrator on {host}:{port}")
    logger.info(f"📡 Safety Agent: {OrchestratorExecutor.SAFETY_AGENT_URL}")
    logger.info(f"📡 Conversation Agent: {OrchestratorExecutor.CONVERSATION_AGENT_URL}")
    logger.info(f"📡 Memory Agent: {OrchestratorExecutor.MEMORY_AGENT_URL}")

    # Setup A2A Components
    agent_card = get_agent_card(host, port)
    task_store = InMemoryTaskStore()
    agent_executor = OrchestratorExecutor()

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=task_store
    )

    # Build App
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    app = server.build()

    # Add CORS middleware to allow React Dashboard to connect
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
