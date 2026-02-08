# 🚀 Quick Start Guide - GrandCompanion

**Get GrandCompanion running in 5 minutes!**

---

## Prerequisites

### 1. Install Ollama (LLM Server)

**macOS/Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**:
Download from [ollama.com](https://ollama.com/download)

**Verify installation**:
```bash
ollama --version
```

### 2. Pull the LLM Model

```bash
ollama pull llama3.1:8b
```

This downloads the 8B parameter Llama 3.1 model (~4.7GB).

**Verify Ollama is running**:
```bash
curl http://localhost:11434
# Should return: Ollama is running
```

### 3. Install Python 3.11+

```bash
python3 --version
# Should show 3.11 or higher
```

If not installed:
- **macOS**: `brew install python@3.11`
- **Ubuntu**: `sudo apt install python3.11`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### 4. Install Node.js 18+

```bash
node --version
# Should show v18 or higher
```

If not installed:
- **macOS**: `brew install node`
- **Ubuntu**: `sudo apt install nodejs npm`
- **Windows**: Download from [nodejs.org](https://nodejs.org/)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd GrandCompanion
```

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Dependencies installed**:
- `a2a` - Agent-to-Agent protocol
- `litellm` - LLM interface
- `google-adk` - Agent Development Kit
- `uvicorn` - ASGI server
- `httpx` - HTTP client

### Step 3: Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

---

## Running GrandCompanion

### Option 1: Automated Startup (Recommended)

**Start all services with one command**:

```bash
# From project root
cd backend
./start_all.sh
```

This starts:
- ✅ Safety Agent (port 8080)
- ✅ Conversation Agent (port 8081)
- ✅ Orchestrator (port 8082)
- ✅ Memory Agent (port 8083)

**In a new terminal, start the frontend**:

```bash
cd frontend
npm start
```

**Access the app**: http://localhost:3000

### Option 2: Manual Startup (For Debugging)

Open 5 separate terminals:

**Terminal 1: Safety Agent**
```bash
cd backend/src/safety
python server.py
```

**Terminal 2: Conversation Agent**
```bash
cd backend/src/conversation_agent
python server.py
```

**Terminal 3: Memory Agent**
```bash
cd backend/src/memory_agent
python server.py
```

**Terminal 4: Orchestrator**
```bash
cd backend/src/orchestrator
python server.py
```

**Terminal 5: Frontend**
```bash
cd frontend
npm start
```

---

## Verification

### Check All Services Are Running

```bash
# Safety Agent (8080)
curl http://localhost:8080
# Should return: Method Not Allowed

# Conversation Agent (8081)
curl http://localhost:8081
# Should return: Method Not Allowed

# Orchestrator (8082)
curl http://localhost:8082
# Should return: Method Not Allowed

# Memory Agent (8083)
curl http://localhost:8083
# Should return: Method Not Allowed

# Frontend (3000)
curl http://localhost:3000
# Should return: React HTML
```

### Test Ollama Connection

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello"
}'
```

Should return streaming JSON response.

---

## First Interaction

1. **Open Browser**: Navigate to http://localhost:3000
2. **Start Conversation**: Type "Hello, I'm feeling great today!"
3. **Expected Response**:
   - Warm greeting from the assistant
   - MoodSelector widget appears on the right
4. **Try Emergency Contact**: Type "I need to call my son"
5. **Expected Response**:
   - ContactSelector widget appears
   - John (Son) is suggested
   - Large "Call Now" button

---

## Demo Scenarios

### Scenario 1: Mood Tracking
```
You: "I'm feeling sad today"
→ MoodSelector widget appears
→ Click on 😢 sad emoji
→ Assistant responds empathetically
```

### Scenario 2: Emergency Contact
```
You: "I need to call my daughter"
→ ContactSelector widget appears
→ Sarah (Daughter) is highlighted
→ Click "Call Now" to initiate call
```

### Scenario 3: Safety Detection (Medium Risk)
```
You: "I'm confused and don't know where I am"
→ Safety Agent detects confusion (MEDIUM risk)
→ Assistant provides calm, reassuring response
→ MoodSelector widget appears
→ Context updated: cognitive_clarity = "confused"
```

### Scenario 4: Emergency (High Risk)
```
You: "I fell down and my chest hurts"
→ Safety Agent detects emergency (HIGH risk)
→ EmergencyAlert widget appears
→ Auto-dial to emergency contact
→ Incident report generated
```

---

## Troubleshooting

### Problem: Ollama not responding

**Solution**:
```bash
# Start Ollama service
ollama serve

# In another terminal, test
ollama run llama3.1:8b "Hello"
```

### Problem: Agent won't start (Port already in use)

**Solution**:
```bash
# Find process using port 8080 (example)
lsof -ti:8080

# Kill the process
kill -9 <PID>

# Or kill all Python processes
pkill -f "python.*server.py"
```

### Problem: Frontend can't connect to backend

**Solution**:
1. Check all 4 backend agents are running (ports 8080-8083)
2. Check frontend .env file (if exists)
3. Verify CORS is enabled in agents
4. Check browser console for error messages

### Problem: "Method Not Allowed" error in UI

**Cause**: Frontend is hitting wrong endpoint

**Solution**:
Check `frontend/src/hooks/useElderAgent.ts` has correct URL:
```typescript
const ORCHESTRATOR_URL = "http://localhost:8082";
```

### Problem: Context not persisting

**Cause**: Memory Agent not running or crashed

**Solution**:
```bash
# Check Memory Agent logs
tail -f backend/src/memory_agent/memory_agent.log

# Restart Memory Agent
cd backend/src/memory_agent
python server.py
```

### Problem: Safety Agent timeout

**Cause**: LLM taking too long to respond

**Solution**:
1. Check Ollama is running: `ollama ps`
2. Increase timeout in `src/orchestrator/server.py`:
   ```python
   async with httpx.AsyncClient(timeout=60.0) as httpx_client:
   ```

---

## Stopping Services

### Stop All Services

**Automated**:
```bash
# From backend directory
./stop_all.sh
```

**Manual**:
```bash
# Kill all backend agents
pkill -f "python.*server.py"

# Stop frontend
# In the npm terminal: Ctrl+C
```

### Stop Individual Service

```bash
# Find process ID
ps aux | grep "safety/server.py"

# Kill specific process
kill <PID>
```

---

## Next Steps

✅ **You're all set!** GrandCompanion is running.

**What to do next**:

1. **Try Demo Scenarios** (see above)
2. **Read Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. **Understand Context System**: [docs/CONTEXT_ARCHITECTURE.md](docs/CONTEXT_ARCHITECTURE.md)
4. **Explore Safety Tools**: [docs/SAFETY_TOOLS_GUIDE.md](docs/SAFETY_TOOLS_GUIDE.md)
5. **Customize Contacts**: Edit `frontend/src/components/widgets/ContactSelector.tsx`

---

## Development Tips

### Hot Reload

**Frontend**: Changes auto-reload (React Fast Refresh)

**Backend**: Restart agent after code changes
```bash
# Example: Restart Safety Agent
pkill -f "safety/server.py"
cd backend/src/safety
python server.py
```

### View Logs

```bash
# Safety Agent
tail -f backend/src/safety/safety.log

# Orchestrator
tail -f backend/src/orchestrator/orchestrator.log

# Memory Agent
tail -f backend/src/memory_agent/memory_agent.log
```

### Debug Mode

Add environment variable before starting agent:
```bash
export DEBUG=1
python server.py
```

---

## Performance Optimization

### For Low-End Hardware

1. **Use smaller LLM**:
   ```bash
   ollama pull llama3.1:3b
   ```
   Update agents to use `llama3.1:3b` instead of `:8b`

2. **Reduce context window**:
   Edit `backend/src/memory_agent/context_manager.py`:
   ```python
   conversation_history = []  # Last 5 turns instead of 10
   ```

3. **Disable safety agent for demo**:
   Comment out safety check in `backend/src/orchestrator/server.py`

---

## FAQ

**Q: Do I need internet for this to work?**
A: No! Once Ollama model is downloaded, everything runs locally.

**Q: How much RAM do I need?**
A: Minimum 8GB, recommended 16GB for llama3.1:8b

**Q: Can I use a different LLM?**
A: Yes! Edit `backend/src/conversation_agent/server.py` and change model name.

**Q: Where is data stored?**
A: In-memory only. Data clears on restart. For persistence, see docs/ARCHITECTURE.md

**Q: Can I deploy this to production?**
A: Yes, but add:
  - Database for context storage (AlloyDB recommended)
  - Authentication system
  - HTTPS/TLS encryption
  - Rate limiting
  - Error monitoring

---

## Getting Help

- **Documentation**: Check [docs/](docs/) directory
- **Issues**: Open a GitHub issue
- **Architecture Questions**: Read [docs/CONTEXT_ARCHITECTURE.md](docs/CONTEXT_ARCHITECTURE.md)

---

**🎉 Enjoy building with GrandCompanion!**
