# conversation_server.py
import logging
import uvicorn
import json
import os
import requests
from a2a.utils.errors import ServerError
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TaskState
from a2a.utils import new_task, completed_task, new_artifact, new_agent_text_message
from a2a.types import Part, TextPart,UnsupportedOperationError
from a2a.server.tasks import TaskUpdater



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConversationAgent")

class ConversationExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Entry point for the agent.
        1. Extract the user's input.
        2. Generate a warm response.
        3. Send the response back.
        """
        try:
            # 1. Get input
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            user_input = context.get_user_input()
            logger.info(f"📨 Received: {user_input}")

            # 2. Generate Response (Mocked LLM for testing simplicity)
            # In production, replace this function with a call to Gemini
            response_text = self.generate_llm_response(user_input)
            

            
            # 3. Send Completion
            logger.info(f"📤 Sending: {response_text}")
            completed = completed_task(
                task.id,
                task.context_id,
                [new_artifact([Part(root=TextPart(text=response_text))], "response")],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"Error: {e}")
            # Fail gracefully
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(TaskState.failed, final=True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())

    def generate_llm_response(self, input_json: str) -> str:
        """
        Generates a response via a local Ollama model.
        """
        try:
            # The Orchestrator sends JSON with 'user_text', 'memory_context', etc.
            data = json.loads(input_json)
            user_text = data.get("user_text", "")
            memory = data.get("memory_context", "")
            
            prompt = (
                "You are a warm, empathetic companion for an older adult. "
                "Reply gently, briefly, and encouragingly.\n\n"
                f"User: {user_text}\n"
                f"Memory context: {memory}\n"
                "Assistant:"
            )

            model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            url = f"{base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip() or "[Warm Tone] I'm here with you."
        except json.JSONDecodeError:
            # Fallback if raw text is sent
            return f"[Warm Tone] I hear you saying: {input_json}"
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return "[Warm Tone] I'm here with you. Tell me more, dear."

def get_agent_card(host="0.0.0.0", port=8081):
    ''' Create agent card of the conversation Agent'''
    return AgentCard(
        name="Warm Conversation Agent",
        description=(
            "A conversational companion focused on empathetic, supportive, and emotionally-aware dialogue. "
            "This agent reflects user input, maintains a warm tone, and optionally incorporates prior memory context. "
            "It does not perform task execution, planning, or factual reasoning."
        ),
        url=f"http://{host}:{port}/",
        version="1.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"],
            output_modes=["text"],
            streaming=False
        ),
        skills=[
            AgentSkill(
                id="empathetic_chat",
                name="Empathetic Chat",
                description=(
                    "Engages users in warm, emotionally supportive conversation. "
                    "Responds with reflective listening, gentle prompts, and compassionate language."
                ),
                examples=[
                    "User feels unsure about a decision and wants emotional reassurance",
                    "User shares a personal thought and expects a warm response",
                    "User wants casual, friendly conversation without advice"
                ],
                tags=[
                    "conversation",
                    "empathy",
                    "tone-adjustment",
                    "non-judgmental",
                    "memory-aware"
                ],
            )
        ]
    )


if __name__ == "__main__":
    # Run on port 8081 to avoid conflict with other agents
    PORT = 8081
    agent_card = get_agent_card(port=PORT)
    executor = ConversationExecutor()
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()
    
    print(f"Start Conversation Agent on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
