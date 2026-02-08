# 📁 GrandCompanion Project Structure

## Directory Tree

```
GrandCompanion/
│
├── README.md                       ⭐ START HERE - Main project overview
├── QUICK_START.md                  🚀 5-minute setup guide
├── LICENSE                         📄 MIT License
├── PROJECT_STRUCTURE.md            📁 This file
│
├── backend/                        🐍 Python backend (4 agents)
│   ├── README.md                   Backend architecture & setup
│   ├── requirements.txt            Python dependencies
│   ├── start_all.sh               ⚡ Start all agents (executable)
│   ├── stop_all.sh                🛑 Stop all agents (executable)
│   │
│   └── src/
│       ├── orchestrator/          🎯 Main routing agent (Port 8082)
│       │   ├── server.py          Context-first orchestration
│       │   ├── agent.py           A2A helpers
│       │   └── orchestrator.log   Runtime logs
│       │
│       ├── safety/                🛡️ Crisis detection (Port 8080)
│       │   ├── server.py          Safety agent with 8 tools
│       │   └── safety.log         Safety monitoring logs
│       │
│       ├── conversation_agent/    💬 Response generation (Port 8081)
│       │   ├── server.py          Empathetic responses
│       │   └── conversation.log   Chat logs
│       │
│       └── memory_agent/          🧠 Context management (Port 8083)
│           ├── server.py          A2A wrapper
│           ├── context_manager.py ⭐ Three-layer context system
│           └── memory.log         Context operation logs
│
├── frontend/                       ⚛️ React 18 + TypeScript
│   ├── README.md                   (Original React README)
│   ├── README_GRANDCOMPANION.md    Frontend guide
│   ├── package.json                Dependencies
│   ├── tsconfig.json               TypeScript config
│   │
│   ├── public/                     Static assets
│   │   └── index.html
│   │
│   └── src/
│       ├── App.tsx                 Root component
│       ├── index.tsx               Entry point
│       │
│       ├── components/
│       │   ├── ConversationMode.tsx   Main chat interface
│       │   ├── ChatPanel.tsx          Message list + input
│       │   ├── WidgetPanel.tsx        Dynamic widget container
│       │   │
│       │   └── widgets/               🎛️ Smart widgets
│       │       ├── MoodSelector.tsx           😊 5 large emoji buttons
│       │       ├── ContactSelector.tsx        📞 Emergency calling
│       │       ├── ActivitySuggestions.tsx    🎨 Activity cards
│       │       └── ReminderList.tsx           💊 Medication tracker
│       │
│       ├── hooks/
│       │   └── useElderAgent.ts    A2A client hook
│       │
│       └── styles/
│           └── *.css               Elder-friendly styling
│
├── docs/                           📚 Technical documentation
│   ├── ARCHITECTURE.md             System architecture overview
│   ├── CONTEXT_ARCHITECTURE.md     ⭐ Three-layer context (secret sauce)
│   ├── SAFETY_TOOLS_GUIDE.md       Safety agent tools & workflows
│   └── CONTACT_SYSTEM_GUIDE.md     Emergency contact system
│
├── demos/                          🎬 Demo materials
│   ├── screenshots/                UI screenshots (TODO)
│   │   ├── chat_interface.png
│   │   ├── contact_widget.png
│   │   └── emergency_alert.png
│   │
│   └── test_scripts/               Test conversation flows
│       └── demo_scenarios.py       (TODO)
│
└── scripts/                        🔧 Utility scripts
    ├── test_context.py             Test context architecture
    └── health_check.sh             Verify all services running
```

## Key Files by Purpose

### 🎯 For Hackathon Judges

**Start Here**:
1. **README.md** - Project overview, problem/solution, features, demo scenarios
2. **QUICK_START.md** - 5-minute setup to see it running
3. **docs/CONTEXT_ARCHITECTURE.md** - Our technical innovation (context system)

**Documentation**:
- **backend/README.md** - Multi-agent architecture
- **frontend/README_GRANDCOMPANION.md** - Elder-friendly UI design
- **docs/SAFETY_TOOLS_GUIDE.md** - Crisis detection system

### 🛠️ For Setup

**Installation**:
1. `backend/requirements.txt` - Install Python dependencies
2. `frontend/package.json` - Install Node dependencies

**Running**:
1. `backend/start_all.sh` - Start all 4 agents
2. `frontend/` - Run `npm start`

### 💻 For Developers

**Backend Core**:
- `backend/src/memory_agent/context_manager.py` - **The secret sauce** (3-layer context)
- `backend/src/orchestrator/server.py` - Context-first routing
- `backend/src/safety/server.py` - Crisis detection with 8 tools

**Frontend Core**:
- `frontend/src/components/ConversationMode.tsx` - Main interface
- `frontend/src/components/WidgetPanel.tsx` - Dynamic widget system
- `frontend/src/hooks/useElderAgent.ts` - Backend communication

**Widgets**:
- `frontend/src/components/widgets/ContactSelector.tsx` - ⭐ Emergency calling
- `frontend/src/components/widgets/MoodSelector.tsx` - Emotional tracking
- `frontend/src/components/widgets/ActivitySuggestions.tsx` - Activity cards
- `frontend/src/components/widgets/ReminderList.tsx` - Medication reminders

## File Count Summary

```
Total Files: ~100
├── Python Backend: ~20 files
├── React Frontend: ~50 files
├── Documentation: ~10 files
├── Configuration: ~10 files
└── Scripts: ~5 files
```

## Lines of Code

```
Backend (Python):   ~5,000 LOC
Frontend (React):   ~3,000 LOC
Documentation:      ~2,500 LOC
Total:             ~10,500 LOC
```

## Dependencies

### Backend
- **a2a**: Agent-to-Agent protocol
- **litellm**: LLM interface
- **google-adk**: Agent Development Kit
- **uvicorn**: ASGI server
- **httpx**: HTTP client

### Frontend
- **react**: ^18.0.0
- **react-dom**: ^18.0.0
- **typescript**: ^5.0.0
- **@types/react**: ^18.0.0
- **lucide-react**: Icons

### External Services
- **Ollama**: Local LLM server (llama3.1:8b)

## Port Allocation

```
8080 - Safety Agent
8081 - Conversation Agent
8082 - Orchestrator (main entry point)
8083 - Memory Agent
3000 - React Frontend
11434 - Ollama LLM Server
```

## Logs Location

All agent logs are written to their respective directories:

```bash
backend/src/safety/safety.log
backend/src/conversation_agent/conversation.log
backend/src/orchestrator/orchestrator.log
backend/src/memory_agent/memory.log
```

## Important Notes

### ⭐ Start Here for Judges
1. Read [README.md](README.md) - 5 min overview
2. Follow [QUICK_START.md](QUICK_START.md) - Get it running
3. Try demo scenarios from README
4. Read [docs/CONTEXT_ARCHITECTURE.md](docs/CONTEXT_ARCHITECTURE.md) for technical depth

### 🏆 Key Innovation
**[context_manager.py](backend/src/memory_agent/context_manager.py)** - This is our secret sauce! Three-layer context system that gives agents perfect memory.

### 🎨 Design Highlights
**[ContactSelector.tsx](frontend/src/components/widgets/ContactSelector.tsx)** - Shows elder-friendly UI: large buttons, smart suggestions, one-tap calling.

### 🛡️ Safety System
**[server.py](backend/src/safety/server.py)** - 8 tools for crisis detection, intervention, and emergency response.

---

**Questions?** Check [README.md](README.md) or [QUICK_START.md](QUICK_START.md)
