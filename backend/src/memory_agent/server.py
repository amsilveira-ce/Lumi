# memory_server.py - Memory Agent for GrandCompanion (Wrapper for Context Manager)
import logging
import uvicorn
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
import json
import os

# Import the centralized Context Manager
# Use absolute import since we run server.py directly
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from context_manager import ContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryAgent")


class MemoryExecutor(AgentExecutor):
    """
    Memory Agent wrapper for the Context Manager (Single Source of Truth).

    This provides backward compatibility while delegating to context_manager.py
    for the full three-layer context architecture.

    Supports both legacy actions (store/retrieve) and new context operations.
    """

    def __init__(self):
        super().__init__()
        # Delegate to Context Manager for all operations
        self.context_manager = ContextManager()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Handles memory operations by delegating to Context Manager.
        """
        try:
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)

            user_input = context.get_user_input()
            logger.info(f"📨 [MEMORY] Received: {user_input}")

            # Delegate to Context Manager
            response_text = await self.process_memory_request(user_input)

            logger.info(f"📤 [MEMORY] Sending: {response_text[:200]}...")

            completed = completed_task(
                task.id,
                task.context_id,
                [new_artifact([Part(root=TextPart(text=response_text))], "memory_result")],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"❌ [MEMORY] Error: {e}", exc_info=True)
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"Memory operation failed: {str(e)}",
                    context.context_id,
                    context.task_id,
                ),
                final=True,
            )

    async def process_memory_request(self, text: str) -> str:
        """
        Processes memory operations by delegating to Context Manager.

        Supports:
        - Legacy actions: store, retrieve (backward compatibility)
        - New actions: get_context, update_turn, update_state, get_history, update_profile
        """
        try:
            data = json.loads(text)
            action = data.get("action")

            # Backward compatibility: Convert legacy "store" to "update_turn"
            if action == "store":
                user_id = data.get("user_id", "default")
                content = data.get("data", "")

                # Parse stored data (usually "User: ...\nAssistant: ...")
                lines = content.split("\n")
                user_message = ""
                assistant_message = ""

                for line in lines:
                    if line.startswith("User:"):
                        user_message = line.replace("User:", "").strip()
                    elif line.startswith("Assistant:"):
                        assistant_message = line.replace("Assistant:", "").strip()

                # Convert to update_turn action
                new_request = json.dumps({
                    "action": "update_turn",
                    "user_id": user_id,
                    "user_message": user_message,
                    "assistant_message": assistant_message
                })

                logger.info(f"🔄 [MEMORY] Converting legacy 'store' to 'update_turn'")
                return await self.context_manager.process_context_request(new_request)

            # Backward compatibility: Convert legacy "retrieve" to "get_history"
            elif action == "retrieve":
                user_id = data.get("user_id", "default")

                # Get conversation history from context
                history_request = json.dumps({
                    "action": "get_history",
                    "user_id": user_id
                })

                history_json = await self.context_manager.process_context_request(history_request)
                history = json.loads(history_json)

                # Format as legacy string format
                if not history:
                    return "No memories found for this user."

                formatted_memories = []
                for turn in history[-3:]:  # Last 3 turns
                    role = "User" if turn["role"] == "user" else "Assistant"
                    formatted_memories.append(f"{role}: {turn['content']}")

                result = "\n\n".join(formatted_memories)
                logger.info(f"🔄 [MEMORY] Converting legacy 'retrieve' to formatted history")
                return result

            # New context operations: Delegate directly to Context Manager
            else:
                logger.info(f"📦 [MEMORY] Delegating '{action}' to Context Manager")
                return await self.context_manager.process_context_request(text)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in memory request: {text}")
            return json.dumps({"error": "Invalid memory request format"})
        except Exception as e:
            logger.error(f"Memory processing error: {e}", exc_info=True)
            return json.dumps({"error": f"Memory error: {str(e)}"})

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())


def get_agent_card(host: str = "0.0.0.0", port: int = 8083) -> AgentCard:
    """Defines the capabilities of the Memory Agent (Context Manager wrapper)."""
    return AgentCard(
        name="Memory Agent",
        description=(
            "Centralized context management system - SINGLE SOURCE OF TRUTH for GrandCompanion. "
            "Maintains conversation history, active topics, user profile, and current state. "
            "ALL agents must retrieve context from here before processing. "
            "Supports legacy memory operations for backward compatibility."
        ),
        url=f"http://{host}:{port}/",
        version="2.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"], output_modes=["text"], streaming=False
        ),
        skills=[
            # NEW CONTEXT OPERATIONS (Primary)
            AgentSkill(
                id="get_context",
                name="Get Full Context Package",
                description="Returns complete context: conversation history, active topics, user profile, current state. REQUIRED before any agent invocation.",
                examples=["Get context for routing decision", "Fetch user state before safety check"],
                tags=["context", "orchestration", "coordination", "required"],
            ),
            AgentSkill(
                id="update_turn",
                name="Update Conversation Turn",
                description="Adds new turn to history, updates topics, refreshes state. Call after each user-agent exchange.",
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
            AgentSkill(
                id="update_profile",
                name="Update User Profile",
                description="Updates user profile data (age, conditions, emergency contacts, preferences).",
                examples=["Save emergency contacts from onboarding", "Update user preferences"],
                tags=["profile", "settings", "personalization"],
            ),
            # LEGACY OPERATIONS (Backward Compatibility)
            AgentSkill(
                id="store_memory",
                name="Store Memory (Legacy)",
                description="Legacy operation: Stores conversation snippets. Now converted to update_turn internally.",
                examples=["Save user's medication schedule", "Remember family details"],
                tags=["storage", "memory", "persistence", "legacy"],
            ),
            AgentSkill(
                id="retrieve_memory",
                name="Retrieve Memory (Legacy)",
                description="Legacy operation: Retrieves relevant memories. Now returns formatted conversation history internally.",
                examples=["Find memories about family", "Recall user's routines"],
                tags=["retrieval", "search", "context", "legacy"],
            ),
        ],
    )


def main():
    """Starts the Memory Agent Server on port 8083."""
    host = "0.0.0.0"
    port = int(os.environ.get("MEMORY_PORT", 8083))

    logger.info(f"🚀 Starting Memory Agent on {host}:{port}")

    agent_card = get_agent_card(host, port)
    task_store = InMemoryTaskStore()
    agent_executor = MemoryExecutor()

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