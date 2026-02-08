# (Imports same as your ingredientmatcheragent/agent_server.py)
import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import new_task, completed_task, new_artifact
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
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
import json
import grpc
import os
import asyncio
from google.genai import types as genai_types
from google.adk.agents import Agent 
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.memory import InMemoryMemoryService 
import datetime
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SafetyAgent")

# ==========================================
# 1. TOOL: Context Retrieval
# ==========================================

def get_emergency_context(user_id: str) -> dict:
    """
    Retrieves static context about the user (Location, Contacts).
    Does NOT assess risk.
    """
    return {
        "user_name": "Grandpa Joe",
        "current_time": datetime.datetime.now().strftime("%H:%M"),
        "location": "Home - 123 Maple St",
        "emergency_contacts": [
            {"name": "Tommy", "phone": "555-0199", "relation": "Grandson", "preferred_method": "call"},
            {"name": "Dr. Smith", "phone": "555-0900", "relation": "Doctor", "preferred_method": "message"}
        ],
        "medical_notes": "History of heart arrhythmia."
    }


def analyze_safety(text: str) -> dict:
    """
    Analyzes text for health crises, abuse, or severe distress using keyword matching.
    
    Args:
        text: The user input text to analyze.
        
    Returns:
        dict: A dictionary containing is_safe boolean, reason, and response_suggestion.
    """
    logger.info(f"🛡️ [SAFETY_TOOL] Analyzing: {text}")
    
    # Crisis keywords for MVP/Hackathon
    crisis_keywords = ["fall", "fell", "chest pain", "hurt myself", "suicide", "emergency", "blood", "help me"]
    is_safe = True
    reason = "User appears stable."
    response_suggestion = ""

    text_lower = text.lower()
    for word in crisis_keywords:
        if word in text_lower:
            is_safe = False
            reason = f"Detected crisis keyword: {word}"
            response_suggestion = "I am concerned about what you just said. I am notifying your emergency contact immediately. Please stay on the line."
            break

    result = {
        "is_safe": is_safe,
        "reason": reason,
        "response_suggestion": response_suggestion
    }
    
    # Log unsafe detections immediately
    if not is_safe:
        logger.warning(f"🚨 [SAFETY_TOOL] CRISIS DETECTED: {reason}")
        
    return result


# ==========================================
# 2. ADK Manager (Singleton Logic)
# ==========================================

class ADKManager:
    """
    Manages the lifecycle of the ADK Runner, Session, and Memory services.
    Ensures we don't re-initialize the LLM on every request.
    """
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.runner = None
        self._initialize_runner()

    def _initialize_runner(self):
        # Configuration
        model_name = os.environ.get("SAFETY_MODEL", "ollama_chat/gpt-oss:20b")
        logger.info(f"🤖 Initializing ADK with model: {model_name}")

        # Define the Agent
        safety_agent = Agent(
            name="safety_monitor",
            model=LiteLlm(model=model_name),
            description="A real-time safety monitor that analyzes conversation for crises.",
            instruction=(
               "You are the Safety Decision Engine. You must output JSON ONLY.\n"
                "You must follow this flowchart state machine:\n\n"

                "STEP 1: FETCH CONTEXT\n"
                "- Always call `get_emergency_context` to see contacts and time.\n\n"

                "STEP 2: DETERMINE RISK LEVEL (based on user text)\n"
                "- LOW: Casual chat. -> Action: 'continue_calm'\n"
                "- MEDIUM: Sadness, loneliness, confusion. -> Action: 'offer_support'\n"
                "- HIGH: Pain, falls, medical issues, panic. -> Go to STEP 3.\n\n"

                "STEP 3: HANDLE HIGH RISK (Conversation Flow)\n"
                "- IF this is the FIRST mention of danger:\n"
                "  -> Action: 'confirm_emergency'\n"
                "  -> Reason: 'User reported high risk situation. Seeking confirmation.'\n"
                "- IF user confirms 'YES' (e.g., 'yes', 'please', 'help'):\n"
                "  -> Action: 'execute_action'\n"
                "  -> Method: 'call' or 'message' (based on contact preference)\n"
                "- IF user says 'NO' (e.g., 'I'm fine', 'wait'):\n"
                "  -> Action: 'stay_present_monitor'\n\n"
            ),
            tools=[analyze_safety, get_emergency_context]
        )

        # Initialize Runner
        self.runner = Runner(
            agent=safety_agent,
            app_name="safety_service",
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        logger.info("✅ ADK Runner initialized successfully")

    async def process_message(self, user_id: str, session_id: str, text: str) -> str:
        """
        Processes a message through the ADK runner.
        """
        # Ensure session exists
        try:
            await self.session_service.get_session(user_id=user_id, session_id=session_id)
        except Exception:
            await self.session_service.create_session(
                app_name="safety_service", 
                user_id=user_id, 
                session_id=session_id
            )

        # Create content object
        content = genai_types.Content(
            role="user", 
            parts=[genai_types.Part(text=text)]
        )

        # Run the agent
        # We need to collect the final response from the event stream
        response_text = ""
        try:
            # Note: Depending on specific ADK version, runner.run might be async or sync generator
            # Adapting to standard ADK patterns:
            steps = self.runner.run(
                user_id=user_id, 
                session_id=session_id, 
                new_message=content
            )
            
            # Iterate through steps to find the final response
            for step in steps:
                if hasattr(step, "is_final_response") and step.is_final_response():
                    if hasattr(step, "content") and step.content and step.content.parts:
                        response_text = step.content.parts[0].text
                        
            if not response_text:
                # Fallback if the model didn't output text (e.g. only tool use)
                # In this specific case, we force the model to output the tool result
                response_text = json.dumps({"is_safe": True, "reason": "Agent provided no output", "response_suggestion": ""})

        except Exception as e:
            logger.error(f"Error in ADK execution: {e}")
            raise

        return response_text

# Initialize global manager
adk_manager = ADKManager()


class SafetyExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            task = context.current_task

            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            user_input = context.get_user_input()
            logger.info(f"📨 [A2A] Received Request: {user_input}")

            # 3. Execution (Call ADK)
            # We use context.context_id as the session_id to maintain conversation threads
            # We use a default user_id or extract from metadata if available
            user_id = "default_user" 
            session_id = context.context_id

            response_text = await adk_manager.process_message(
                user_id=user_id, 
                session_id=session_id, 
                text=user_input
            )

            logger.info(f"📤 [A2A] Generated Response: {response_text}")

            completed = completed_task(
                task.id,
                task.context_id,
                [
                    new_artifact(
                        [Part(root=TextPart(text=response_text))],
                        "safety_analysis_result",
                    )
                ],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"❌ Execution Error: {e}")
            # Fail gracefully
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(
                TaskState.failed, 
                new_agent_text_message(f"Safety Analysis Failed: {str(e)}", context.context_id, context.task_id),
                final=True
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())

            

def get_agent_card(host: str, port: int) -> AgentCard:
    """Defines the capabilities of the Safety Agent for the A2A network."""

    return AgentCard(
        name="Safety Agent",
        description=(
            "Real-time crisis detection, emergency escalation, and safety monitoring "
            "agent for elder-care scenarios. Activated only by the Orchestrator."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"],
            output_modes=["text"],
            streaming=False
        ),
        skills=[
            AgentSkill(
                id="analyze_safety",
                name="Analyze Safety Context",
                description=(
                    "Analyzes user input and context for signs of distress, emergency, "
                    "or safety risk. Returns structured risk assessment."
                ),
                examples=[
                    "I fell down and can’t get up",
                    "I feel dizzy and my chest hurts",
                    "I am scared and don’t feel well"
                ],
                tags=["crisis-detection", "risk-analysis", "elder-care"]
            ),
            AgentSkill(
                id="crisis_intervention",
                name="Crisis Intervention",
                description=(
                    "Provides calm, reassuring responses and grounding guidance "
                    "during medium-risk situations without escalation."
                ),
                examples=[
                    "Please stay with me, take a slow breath",
                    "You are not alone, I am here to help"
                ],
                tags=["mental-health", "de-escalation", "emotional-support"]
            ),
            AgentSkill(
                id="initiate_emergency_action",
                name="Initiate Emergency Action",
                description=(
                    "Initiates emergency actions such as sending alerts or placing calls "
                    "after user confirmation or high-risk determination."
                ),
                examples=[
                    "Call the hospital",
                    "Call my daughter Maria"
                ],
                tags=["emergency", "call-routing", "alerts"]
            ),
            AgentSkill(
                id="generate_emergency_report",
                name="Generate Emergency Report",
                description=(
                    "Generates a concise incident report summarizing the emergency, "
                    "user state, time, and actions taken."
                ),
                examples=[
                    "Emergency summary for caregiver",
                    "Incident report for family contact"
                ],
                tags=["reporting", "audit", "caregiver-support"]
            ),
            AgentSkill(
                id="mark_as_safe",
                name="Mark User as Safe",
                description=(
                    "Marks the situation as resolved and safely de-escalated, "
                    "returning control to the Orchestrator."
                ),
                examples=[
                    "User confirmed they are safe",
                    "Emergency contact resolved the issue"
                ],
                tags=["resolution", "state-management"]
            ),
            AgentSkill(
                id="flag_warning",
                name="Flag Safety Warning",
                description=(
                    "Flags repeated concerning signals for future monitoring "
                    "without triggering emergency escalation."
                ),
                examples=[
                    "Repeated confusion detected",
                    "Multiple distress signals in one day"
                ],
                tags=["monitoring", "preventive-care"]
            )
        ]
    )

   
        

def main():
    """Main entry point."""
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8080))

    logger.info(f"🚀 Starting Safety Agent on {host}:{port}")

    # Setup A2A Components
    agent_card = get_agent_card(host, port)
    task_store = InMemoryTaskStore()
    agent_executor = SafetyExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    # Build App
    server = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )

    app = server.build()
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()