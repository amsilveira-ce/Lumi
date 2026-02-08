from google.adk.agents import Agent
import asyncio
import httpx
from google.adk.models.lite_llm import LiteLlm
from a2a.client import A2ACardResolver, ClientFactory, create_text_message_object
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol
import logging
import json


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# --- Helper: Generic A2A Caller (Reused from your uploaded agent.py) ---
async def call_a2a_agent(agent_url: str, message_text: str) -> dict:
    """Helper to send a message to an A2A agent and return the response text."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            card_resolver = A2ACardResolver(httpx_client, agent_url)
            agent_card = await card_resolver.get_agent_card()
            
            config = ClientConfig(httpx_client=httpx_client, supported_transports=[TransportProtocol.jsonrpc])
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            message = create_text_message_object(content=message_text)
            final_response = None
            async for response_chunk in client.send_message(message):
                final_response = response_chunk

            if not final_response:
                return {"status": "error", "error": "No response"}

            # Extract text logic (simplified from your example for brevity)
            response_text = ""
            if hasattr(final_response, "parts"):
                for part in final_response.parts:
                    if hasattr(part, "root") and hasattr(part.root, "text"):
                        response_text += part.root.text
                    elif hasattr(part, "text"):
                        response_text += part.text
            
            return {"status": "success", "response_text": response_text}
    except Exception as e:
        logger.error(f"A2A call failed: {e}")
        return {"status": "error", "error": str(e)}

def check_safety(user_text: str) -> dict:
    """
    Checks if the user's input indicates a crisis or unsafe situation.
    ALWAYS call this tool first.
    """
    logger.info(f"🛡️ [ORCHESTRATOR] Checking safety for: {user_text}")
    result = asyncio.run(call_a2a_agent("http://safety-agent:8080", user_text))
    
    # Parse the JSON response from the Safety Agent
    try:
        safety_data = json.loads(result.get("response_text", "{}"))
        return safety_data
    except json.JSONDecodeError:
        return {"is_safe": True, "reason": "Parse error, assuming safe"}

def consult_memory(user_id: str, context_query: str) -> str:
    """
    Retrieves personal anecdotes and relationship details relevant to the conversation.
    Call this to personalize the response.
    """
    logger.info(f"🧠 [ORCHESTRATOR] Querying memory for: {context_query}")
    query_payload = json.dumps({"action": "retrieve", "user_id": user_id, "query": context_query})
    result = asyncio.run(call_a2a_agent("http://memory-agent:8080", query_payload))
    return result.get("response_text", "No memory found.")

def generate_companion_response(user_text: str, memory_context: str, mood: str) -> str:
    """
    Delegates the final response generation to the specialist persona agent.
    """
    logger.info(f"💬 [ORCHESTRATOR] Requesting companion response")
    payload = json.dumps({
        "user_text": user_text,
        "memory_context": memory_context,
        "mood": mood
    })
    result = asyncio.run(call_a2a_agent("http://conversation-agent:8080", payload))
    return result.get("response_text", "I'm having trouble thinking right now, dear.")

def save_new_memory(user_id: str, text_to_save: str) -> str:
    """
    Saves important details (names, events, preferences) to long-term memory.
    """
    logger.info(f"💾 [ORCHESTRATOR] Saving memory")
    payload = json.dumps({"action": "store", "user_id": user_id, "data": text_to_save})
    asyncio.run(call_a2a_agent("http://memory-agent:8080", payload))
    return "Memory saved."

orchestrator_agent = Agent(
    name="elder_care_orchestrator",
    model=LiteLlm(model="ollama_chat/llama3.1:8b"), # Or gemini-1.5-pro
    description="Central router for an elder companion AI.",
    instruction=(

                "You are a Safety Orchestrator. Your goal is to assess danger using the `get_emergency_context` tool.\n"
                "PROTOCOL:\n"
                "1. Receive the user's text and User ID.\n"
                "2. Call `get_emergency_context(user_id, user_text)` immediately.\n"
                "3. The tool will return a JSON object with `risk_level` and `recommended_action`.\n"
                "4. Your FINAL response must be ONLY that JSON object as a string.\n"
            
    ),
    tools=[check_safety, consult_memory, generate_companion_response, save_new_memory],
)