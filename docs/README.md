# GrandCompanion Multi-Agent System

A compassionate AI companion system for elderly users, featuring safety monitoring, empathetic conversation, and personalized memory.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         React Dashboard (localhost:3000)            │
│  ┌──────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │Dashboard │  │Conversation │  │Elder-Specific │  │
│  │  Mode    │  │    Mode     │  │  Onboarding   │  │
│  └──────────┘  └─────────────┘  └───────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/A2A Protocol
                     ▼
┌─────────────────────────────────────────────────────┐
│       Orchestrator (localhost:8082)                 │
│  Routes messages + Manages UI widgets               │
└───────┬─────────────┬─────────────┬─────────────────┘
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌────────────┐ ┌────────────┐
│Safety Agent  │ │Conversation│ │Memory Agent│
│(Port 8080)   │ │Agent       │ │(Port 8083) │
│              │ │(Port 8081) │ │            │
│Crisis        │ │Warm, Empat │ │Stores &    │
│Detection     │ │-hetic      │ │Retrieves   │
│Emergency     │ │Companion   │ │Context     │
│Escalation    │ │            │ │            │
└──────────────┘ └────────────┘ └────────────┘
        │
        ▼
    [Ollama LLM]
   llama3.1:8b
```

## Features

### 🛡️ Safety Agent (Port 8080)
- **Crisis Detection**: Keyword-based detection for falls, chest pain, emergencies
- **Risk Assessment**: LOW/MEDIUM/HIGH risk classification
- **Emergency Protocol**:
  - Confirms with user before escalating
  - Calls emergency contacts
  - Generates incident reports
- **Tools**: `analyze_safety()`, `get_emergency_context()`

### 💬 Conversation Agent (Port 8081)
- **Empathetic Responses**: Warm, supportive tone for elderly users
- **Context-Aware**: Uses memory context for personalization
- **LLM-Powered**: Ollama (llama3.1:8b) for natural conversations
- **Adaptive**: Adjusts based on user's cognitive comfort level

### 🧠 Memory Agent (Port 8083)
- **Storage**: Saves conversation history, preferences, family details
- **Retrieval**: Keyword-based search for relevant memories
- **Personalization**: Provides context to make responses personal
- **In-Memory**: MVP uses dict storage (upgradable to vector DB)

### 🎯 Orchestrator (Port 8082)
- **Safety-First Routing**: Always checks safety before processing
- **Agent Coordination**: Routes to Safety/Conversation/Memory agents
- **UI Widget Management**:
  - Shows MoodSelector when user mentions feelings
  - Shows ActivitySuggestions when user is bored
  - Shows ReminderList for medication/appointments
- **A2A Protocol**: Uses Agent-to-Agent communication standard

## Installation

### Prerequisites
```bash
# Python 3.10+
python --version

# Ollama (for LLM)
ollama pull llama3.1:8b

# Required Python packages
pip install uvicorn a2a-sdk google-genai-adk litellm httpx
```

### Setup
```bash
cd /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/ElderCompanion

# Install dependencies (if needed)
pip install -r requirements.txt  # Create this if needed
```

## Usage

### Start All Agents
```bash
./start_all_agents.sh
```

This starts:
- ✅ Safety Agent on http://localhost:8080
- ✅ Conversation Agent on http://localhost:8081
- ✅ Orchestrator on http://localhost:8082 (Main entry point)
- ✅ Memory Agent on http://localhost:8083

### Stop All Agents
```bash
./stop_all_agents.sh
```

### View Logs
```bash
# Real-time logs
tail -f logs/orchestrator.log
tail -f logs/safety_agent.log
tail -f logs/conversation_agent.log
tail -f logs/memory_agent.log

# All logs together
tail -f logs/*.log
```

## Dashboard Integration

The React Dashboard at http://localhost:3000 connects to the Orchestrator at port 8082.

### Message Format (Dashboard → Orchestrator)
```json
{
  "action": "conversation",
  "message": "I'm feeling sad today",
  "user_id": "grandpa_joe",
  "elder_profile": {
    "cognitive_comfort": "intermediate",
    "emergency_contacts": [...]
  }
}
```

### Response Format (Orchestrator → Dashboard)
```json
{
  "text": "I'm sorry you're feeling sad. Would you like to talk about it?",
  "ui_commands": [
    {
      "action": "show",
      "component": "MoodSelector",
      "props": {"widget_id": "mood_123"}
    }
  ],
  "is_emergency": false
}
```

## API Endpoints

### Orchestrator (http://localhost:8082)

**POST /message**
- Main entry point for all user messages
- Handles conversation, UI feedback, safety checks

**GET /**
- Returns Agent Card (A2A protocol)

### Safety Agent (http://localhost:8080)

**Tools:**
- `analyze_safety(text)` - Analyzes for crisis keywords
- `get_emergency_context(user_id)` - Gets emergency contacts

**Skills:**
- analyze_safety
- crisis_intervention
- initiate_emergency_action
- generate_emergency_report

### Conversation Agent (http://localhost:8081)

**Skills:**
- empathetic_chat - Warm, supportive conversations

**Input:**
```json
{
  "user_text": "Hello, how are you?",
  "memory_context": "User prefers morning walks",
  "mood": "casual"
}
```

### Memory Agent (http://localhost:8083)

**Actions:**
- `store` - Save new memory
- `retrieve` - Query memories

**Examples:**
```json
// Store
{
  "action": "store",
  "user_id": "grandpa_joe",
  "data": "User's daughter Sarah called today"
}

// Retrieve
{
  "action": "retrieve",
  "user_id": "grandpa_joe",
  "query": "family daughter"
}
```

## Safety Protocol Flow

1. **User sends message** → Orchestrator
2. **Orchestrator** → Safety Agent: "Check this message"
3. **Safety Agent analyzes**:
   - Detects "fall", "chest pain", "help me" → HIGH RISK
   - Otherwise → SAFE
4. **If HIGH RISK**:
   - Safety Agent returns: `{is_safe: false, reason: "Detected crisis keyword: fall"}`
   - Orchestrator triggers emergency UI
   - Dashboard shows EmergencyAlert with auto-call
5. **If SAFE**:
   - Routes to Conversation Agent
   - Determines widgets to show
   - Returns response with UI commands

## Widget Triggering Logic

The Orchestrator analyzes user messages to determine which widgets to show:

| Keywords | Widget | Purpose |
|----------|--------|---------|
| feel, sad, happy, anxious, lonely | MoodSelector | Emotion tracking |
| bored, activity, something to do | ActivitySuggestions | Engagement |
| medication, pill, doctor, appointment | ReminderList | Health management |

## Configuration

### Environment Variables
```bash
# Safety Agent
export SAFETY_MODEL="ollama_chat/gpt-oss:20b"

# Conversation Agent
export OLLAMA_MODEL="llama3.1:8b"
export OLLAMA_BASE_URL="http://localhost:11434"

# Orchestrator
export SAFETY_AGENT_URL="http://localhost:8080"
export CONVERSATION_AGENT_URL="http://localhost:8081"
export MEMORY_AGENT_URL="http://localhost:8083"
```

## Development

### Testing Individual Agents

**Test Safety Agent:**
```bash
curl -X POST http://localhost:8080/message \
  -H "Content-Type: application/json" \
  -d '{"content": "I fell down and can'"'"'t get up"}'
```

**Test Conversation Agent:**
```bash
curl -X POST http://localhost:8081/message \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"user_text\": \"Hello\", \"memory_context\": \"\", \"mood\": \"casual\"}"}'
```

**Test Memory Agent:**
```bash
# Store
curl -X POST http://localhost:8083/message \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"action\": \"store\", \"user_id\": \"test\", \"data\": \"User likes coffee\"}"}'

# Retrieve
curl -X POST http://localhost:8083/message \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"action\": \"retrieve\", \"user_id\": \"test\", \"query\": \"coffee\"}"}'
```

**Test Orchestrator:**
```bash
curl -X POST http://localhost:8082/message \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"action\": \"conversation\", \"message\": \"I feel sad\", \"user_id\": \"test\"}"}'
```

## Troubleshooting

### Agents won't start
```bash
# Check if ports are in use
lsof -i :8080
lsof -i :8081
lsof -i :8082
lsof -i :8083

# Kill processes
./stop_all_agents.sh
```

### Ollama not responding
```bash
# Check Ollama service
ollama list

# Start Ollama
ollama serve

# Pull model
ollama pull llama3.1:8b
```

### Agents crash on startup
```bash
# Check logs
cat logs/safety_agent.log
cat logs/conversation_agent.log
cat logs/orchestrator.log
cat logs/memory_agent.log

# Check Python packages
pip list | grep -E "uvicorn|a2a|genai"
```

## Future Enhancements

1. **Real MCP Integration**: Replace mock emergency contacts with Google Contacts API
2. **Vector Memory**: Upgrade Memory Agent to use AlloyDB + embeddings
3. **Voice Input**: Add speech-to-text for voice-first interaction
4. **Multimodal**: Support image inputs (show pictures, recognize faces)
5. **Persistent Storage**: Save memories to database
6. **Analytics Dashboard**: Track user engagement, mood trends
7. **Multi-language**: Support for Spanish, Portuguese, etc.

## Architecture Decisions

### Why A2A Protocol?
- Standard for agent-to-agent communication
- Supports tool use and multi-turn conversations
- Easy to add new agents to the network

### Why Separate Agents?
- **Safety-First**: Dedicated safety agent ensures no crisis is missed
- **Modularity**: Each agent can be upgraded independently
- **Scalability**: Agents can run on different servers
- **Testability**: Easy to test each agent in isolation

### Why Orchestrator Pattern?
- **Single Entry Point**: Dashboard only needs to know one URL
- **Coordination**: Orchestrator manages complex flows
- **UI Control**: Centralized widget decision logic

## License

MIT

## Contact

For questions or support, contact the development team.
