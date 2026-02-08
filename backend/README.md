# GrandCompanion Backend

**Multi-Agent System with Context-Aware Architecture**

## Overview

The backend consists of 4 specialized agents communicating via the A2A (Agent-to-Agent) protocol:

```
┌──────────────┐
│ Orchestrator │ ← Main entry point (8082)
│    (8082)    │
└──────┬───────┘
       │
   ┌───┴───────────┬───────────┬────────────┐
   │               │           │            │
   ▼               ▼           ▼            ▼
┌──────┐      ┌────────┐  ┌────────┐  ┌──────────┐
│Safety│      │Conver- │  │ Memory │  │ Future:  │
│Agent │      │sation  │  │ Agent  │  │   MCP    │
│(8080)│      │ (8081) │  │ (8083) │  │  Agents  │
└──────┘      └────────┘  └────────┘  └──────────┘
```

## Agents

### 1. **Orchestrator** (Port 8082)

**Role**: Main routing agent, context-first orchestration

**Responsibilities**:
- Accept requests from React frontend
- **CRITICAL**: Fetch full context before any agent invocation
- Route to Safety Agent for risk assessment
- Route to Conversation Agent for response generation
- Determine which widgets to show based on context
- Update context with new conversation turns

**Key Files**:
- `src/orchestrator/server.py` - Main orchestrator logic
- `src/orchestrator/agent.py` - A2A agent helpers

**Key Methods**:
- `execute()` - Main entry point
- `check_safety()` - Call Safety Agent with context
- `handle_conversation()` - Call Conversation Agent with context
- `handle_emergency()` - Emergency response flow
- `determine_widgets()` - Context-aware widget selection

### 2. **Safety Agent** (Port 8080)

**Role**: Real-time crisis detection & emergency response

**Responsibilities**:
- Analyze user messages for safety risks
- 3-tier classification: SAFE, MEDIUM, HIGH
- Crisis intervention for MEDIUM risk
- Emergency actions for HIGH risk
- Generate incident reports

**Key Files**:
- `src/safety/server.py` - Safety agent with Google ADK tools

**Tools Available**:
1. `analyze_safety_context` - LLM-based risk assessment
2. `crisis_intervention` - Empathetic support responses (MANDATORY for MEDIUM)
3. `flag_warning` - Track repeated concerns
4. `mark_user_safe` - Close incidents
5. `place_emergency_call` - Auto-dial emergency contacts
6. `send_emergency_message` - SMS/WhatsApp/Email alerts
7. `generate_emergency_report` - Incident documentation
8. `get_emergency_context` - Fetch emergency contacts

**Risk Levels**:
- **SAFE**: Normal conversation
- **MEDIUM**: Confusion, mild distress, loneliness → `crisis_intervention` required
- **HIGH**: Falls, chest pain, severe distress → Emergency actions

### 3. **Conversation Agent** (Port 8081)

**Role**: Generate empathetic, context-aware responses

**Responsibilities**:
- Generate warm, elder-friendly responses
- Use conversation history for continuity
- Respect user preferences (tone, pace)
- Acknowledge active topics in responses

**Key Files**:
- `src/conversation_agent/server.py` - Response generation

**Context Received**:
- Recent conversation history (last 5 turns)
- Active topics (primary + secondary)
- User emotional state
- User preferences (tone, pace, cognitive_comfort)

### 4. **Memory Agent** (Port 8083)

**Role**: Centralized context management (Single Source of Truth)

**Responsibilities**:
- Maintain 3-layer context architecture
- Detect and track conversation topics
- Update user state based on risk assessments
- Provide full context package to all agents

**Key Files**:
- `src/memory_agent/server.py` - A2A wrapper
- `src/memory_agent/context_manager.py` - **Core context logic**

**Three-Layer Architecture**:

1. **Conversation Context**
   ```python
   conversation_history: [
       {"role": "user", "content": "...", "timestamp": "..."},
       {"role": "assistant", "content": "...", "timestamp": "..."}
   ]  # Last 10 turns
   ```

2. **Active Topic Context**
   ```python
   active_topics: {
       "primary": {"topic": "loneliness", "confidence": 0.9, "started_at": "..."},
       "secondary": [{"topic": "family", "confidence": 0.6}]
   }
   ```

3. **User Context**
   ```python
   user_profile: {
       "age": 78,
       "emergency_contacts": [...],
       "preferences": {"tone": "warm", "pace": "slow"}
   },
   current_state: {
       "emotional_state": "calm",
       "safety_status": "safe",
       "cognitive_clarity": "clear"
   }
   ```

**Operations**:
- `get_context` - Returns full 3-layer context (REQUIRED before agent calls)
- `update_turn` - Adds conversation turn, updates topics, refreshes state
- `update_state` - Updates emotional/safety/cognitive state
- `get_history` - Returns conversation history only
- `update_profile` - Updates user demographics and contacts

## A2A Protocol Flow

```
1. Frontend sends message to Orchestrator
   POST http://localhost:8082 (A2A JSONRPC)

2. Orchestrator fetches context from Memory Agent
   GET context → Memory Agent (8083)

3. Orchestrator checks safety with context
   analyze_safety → Safety Agent (8080) [with full context]

4. Based on risk level:
   - HIGH → Emergency flow (alerts, calls)
   - SAFE/MEDIUM → Conversation flow

5. Orchestrator calls Conversation Agent with context
   generate_response → Conversation Agent (8081) [with full context]

6. Orchestrator determines widgets based on message + context

7. Orchestrator updates context with new turn
   update_turn → Memory Agent (8083)

8. Response sent back to Frontend
```

## Running Agents

### Option 1: Start All (Recommended)

```bash
cd backend
./start_all.sh
```

### Option 2: Start Individually

```bash
# Terminal 1
cd src/safety && python server.py

# Terminal 2
cd src/conversation_agent && python server.py

# Terminal 3
cd src/memory_agent && python server.py

# Terminal 4
cd src/orchestrator && python server.py
```

## Testing Agents

### Test Memory Agent Context

```bash
curl -X POST http://localhost:8083 \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{
        "root": {
          "text": "{\"action\":\"get_context\",\"user_id\":\"test\"}"
        }
      }]
    }
  }'
```

### Test Safety Agent

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{
        "root": {
          "text": "{\"message\":\"I fell down and can'\''t get up\"}"
        }
      }]
    }
  }'
```

## Configuration

### Environment Variables

Create `.env` file in each agent directory:

```bash
# src/safety/.env
OLLAMA_URL=http://localhost:11434
MODEL_NAME=llama3.1:8b
LOG_LEVEL=INFO

# src/orchestrator/.env
SAFETY_AGENT_URL=http://localhost:8080
CONVERSATION_AGENT_URL=http://localhost:8081
MEMORY_AGENT_URL=http://localhost:8083
```

### Changing LLM Model

Edit `src/conversation_agent/server.py`:

```python
# Change from llama3.1:8b to smaller/faster model
model = "llama3.1:3b"  # or "mistral", "phi3", etc.
```

## Logs

Each agent writes logs to its directory:

```bash
# View logs
tail -f src/safety/safety.log
tail -f src/conversation_agent/conversation.log
tail -f src/memory_agent/memory.log
tail -f src/orchestrator/orchestrator.log
```

## Adding New Agents

### 1. Create Agent Directory

```bash
mkdir src/my_new_agent
cd src/my_new_agent
```

### 2. Create `server.py`

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor
# ... implement AgentExecutor subclass
```

### 3. Register with Orchestrator

Edit `src/orchestrator/server.py`:

```python
MY_NEW_AGENT_URL = "http://localhost:8084"

# In handle_conversation or execute:
result = await call_a2a_agent(MY_NEW_AGENT_URL, payload)
```

### 4. Update start_all.sh

Add new agent startup to `start_all.sh`

## Production Deployment

### Security Checklist

- [ ] Add authentication middleware
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Sanitize user inputs
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted origins
- [ ] Add request validation
- [ ] Set up error monitoring (Sentry, etc.)

### Scalability

- [ ] Replace in-memory context store with AlloyDB
- [ ] Add Redis caching layer
- [ ] Use load balancer for multiple Orchestrator instances
- [ ] Implement message queue for async operations
- [ ] Add health check endpoints
- [ ] Set up monitoring (Prometheus + Grafana)

### LLM Optimization

- [ ] Use quantized models for faster inference
- [ ] Implement response caching
- [ ] Add request batching
- [ ] Consider cloud LLM for peak loads (with user consent)

## Troubleshooting

### Agent won't start

**Check port availability**:
```bash
lsof -i :8080  # Safety Agent
lsof -i :8081  # Conversation Agent
lsof -i :8082  # Orchestrator
lsof -i :8083  # Memory Agent
```

**Kill conflicting process**:
```bash
kill -9 <PID>
```

### Context not persisting

**Verify Memory Agent is running**:
```bash
curl http://localhost:8083
```

**Check logs**:
```bash
tail -50 src/memory_agent/memory.log
```

### Safety Agent timeout

**Increase timeout in Orchestrator**:
```python
# src/orchestrator/server.py
async with httpx.AsyncClient(timeout=60.0) as httpx_client:
```

**Use faster LLM model**:
```bash
ollama pull llama3.1:3b
```

## Architecture Decisions

### Why A2A Protocol?

- ✅ Standardized agent communication
- ✅ Built-in JSONRPC support
- ✅ Easy to add new agents
- ✅ Language-agnostic (can add non-Python agents)

### Why Local LLM (Ollama)?

- ✅ Privacy: No data leaves device
- ✅ Cost: No API fees
- ✅ Latency: Fast inference on local hardware
- ✅ Offline: Works without internet

### Why Centralized Context?

- ✅ Single source of truth
- ✅ No context fragmentation
- ✅ Easy to add new context fields
- ✅ Consistent state across all agents

## Further Reading

- **[Context Architecture](../docs/CONTEXT_ARCHITECTURE.md)** - Deep dive into 3-layer system
- **[Safety Tools Guide](../docs/SAFETY_TOOLS_GUIDE.md)** - Safety Agent tools & workflows
- **[A2A Protocol Docs](https://a2a-protocol.github.io/)** - Official A2A documentation

---

**Questions?** Open an issue or check the [main README](../README.md)
