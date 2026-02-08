import asyncio
import httpx
import json
import sys
from a2a.client import A2ACardResolver, ClientFactory, create_text_message_object
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol

# Configuration
# Ensure this matches the port in your agent_server.py (default 8080)
AGENT_URL = "http://localhost:8080"

async def send_test_message(client, text, description):
    print(f"\n--- Test: {description} ---")
    print(f"📤 Sending: '{text}'")
    
    # Create the A2A message object
    message = create_text_message_object(content=text)
    
    try:
        # Send message and await response stream
        response_text = ""
        async for chunk in client.send_message(message):
            # The agent returns an A2A Message object. 
            # We need to extract the text content from its parts.
            if hasattr(chunk, "parts"):
                for part in chunk.parts:
                    if hasattr(part, "root") and hasattr(part.root, "text"):
                        response_text += part.root.text
                    elif hasattr(part, "text"):
                        response_text += part.text
        
        # The Safety Agent returns a JSON string, so let's parse it for readability
        try:
            print("reponse text", response_text)
            result_json = json.loads(response_text)
            print("🤖 Agent Response (Parsed):")
            print(json.dumps(result_json, indent=2))
            
            # Simple verification
            if result_json.get("is_safe") is False:
                print("✅ Correctly identified as UNSAFE.")
            else:
                print("✅ Identified as SAFE.")
                
        except json.JSONDecodeError:
            print(f"⚠️ Raw Response (Not JSON): {response_text}")

    except Exception as e:
        print(f"❌ Error during transmission: {e}")

async def run_tests():
    print(f"🔌 Connecting to Safety Agent at {AGENT_URL}...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            # 1. Resolve the Agent Card (Handshake)
            resolver = A2ACardResolver(httpx_client, AGENT_URL)

            card = await resolver.get_agent_card()
            print(f"✅ Connected to Agent: {card.name} (v{card.version})")

            # 2. Create Client
            config = ClientConfig(
                httpx_client=httpx_client, 
                supported_transports=[TransportProtocol.jsonrpc]
            )
            factory = ClientFactory(config)
            client = factory.create(card)

            # 3. Run Scenarios
            
            # Scenario A: Safe Conversation
            await send_test_message(
                client, 
                "I am planning to visit my grandson tomorrow.", 
                "Normal Conversation"
            )

            # Scenario B: Crisis Keyword
            await send_test_message(
                client, 
                "I think I fell down and I am in a lot of pain.", 
                "Crisis Detection"
            )

    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")
        print("Tip: Is the server running? (python3 src/safetyagent/agent_server.py)")

if __name__ == "__main__":
    asyncio.run(run_tests())