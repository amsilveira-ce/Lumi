# test_conversation_agent.py
import asyncio
import httpx
from a2a.client import A2ACardResolver, ClientFactory, create_text_message_object
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol
import json
import sys

# Configuration
AGENT_URL = "http://localhost:8081"

async def test_agent():
    print(f"🔌 Connecting to Agent at {AGENT_URL}...")
    
    # 1. Define the test payload (What the Orchestrator would send)
    payload = json.dumps({
        "user_text": "I am feeling a bit lonely today.",
        "memory_context": "Grandson Tommy visits on Sundays.",
        "mood": "sad"
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as httpx_client:
            # 2. Resolve the Agent Card (Handshake)
            resolver = A2ACardResolver(httpx_client, AGENT_URL)
            card = await resolver.get_agent_card()
            print(f"✅ Found Agent: {card.name}")

            # 3. Create Client
            config = ClientConfig(httpx_client=httpx_client, supported_transports=[TransportProtocol.jsonrpc])
            factory = ClientFactory(config)
            client = factory.create(card)

            # 4. Send Message
            print(f"📤 Sending Payload: {payload}")
            message = create_text_message_object(content=payload)
            
            response_text = ""
            async for chunk in client.send_message(message):
                # Extract text from the complex A2A response object
                if hasattr(chunk, "parts"):
                    for part in chunk.parts:
                        if hasattr(part, "root") and hasattr(part.root, "text"):
                            response_text += part.root.text
            
            # 5. Output Result
            print("\n" + "="*30)
            print("🤖 AGENT RESPONSE:")
            print(f"{response_text}")
            print("="*30 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Tip: Make sure 'conversation_server.py' is running in another terminal!")

if __name__ == "__main__":
    asyncio.run(test_agent())