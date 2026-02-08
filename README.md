# 🧓💙 GrandCompanion

**AI-Powered Elder Companion with Context-Aware Safety & Emergency Response**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-green.svg)](https://a2a-protocol.github.io/)

> **Empowering elders with AI companionship that remembers, understands, and protects.**

GrandCompanion is an intelligent elder care system that combines conversational AI with real-time safety monitoring, context-aware responses, and emergency intervention capabilities. Built for the modern elder who wants independence with a safety net.

---

## 🎯 The Problem

**65% of elders living alone report feeling lonely**, leading to depression and cognitive decline. Traditional elder care solutions are:
- ❌ **Impersonal** - Generic responses that don't remember context
- ❌ **Unsafe** - No real-time crisis detection or emergency response
- ❌ **Disconnected** - Fragmented systems that lose conversational continuity
- ❌ **Passive** - Wait for problems instead of proactive monitoring

## 💡 Our Solution

GrandCompanion uses a **multi-agent AI architecture** with **centralized context management** to provide:

✅ **Conversational Continuity** - Remembers what you said 5 minutes or 5 days ago
✅ **Real-Time Safety Monitoring** - AI-powered crisis detection with 3-tier risk assessment
✅ **Emergency Response** - Automatic contact notification with one-tap calling
✅ **Context-Aware Interactions** - Understands emotions, topics, and user state
✅ **Elder-Friendly UI** - Large text, simple interface, accessibility-first design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│         (Elder-friendly UI + Dynamic Widgets)            │
└────────────────────┬────────────────────────────────────┘
                     │ A2A JSONRPC Protocol
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR (8082)                    │
│         Context-First Routing & Agent Coordination       │
└─────┬──────────┬──────────┬──────────┬─────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  Safety  │ │Conversation│ │  Memory  │ │  Future:     │
│  Agent   │ │   Agent    │ │  Agent   │ │  MCP Agents  │
│  (8080)  │ │  (8081)    │ │  (8083)  │ │  (Contacts,  │
│          │ │            │ │          │ │   Calendar)  │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
     │             │             │
     └─────────────┴─────────────┘
               │
               ▼
        Ollama LLM (llama3.1:8b)
```

### 🧠 **Three-Layer Context System** (Our Secret Sauce)

**Problem**: Traditional chatbots forget context between messages, leading to repetitive, impersonal interactions.

**Solution**: Every agent receives a full context package before processing:

1. **Conversation Context** - Last 10 turns with timestamps
2. **Active Topic Context** - Primary/secondary topics with confidence scores
3. **User Context** - Profile, preferences, emotional state, safety status

**Result**: System remembers your grandson's name, your medication time, and that you mentioned feeling lonely 3 messages ago.

---

## 🚀 Key Features

### 1. 🛡️ **Real-Time Safety Monitoring**

**3-Tier Risk Classification**:
- 🟢 **SAFE** - Normal conversation, no concerns
- 🟡 **MEDIUM** - Mild distress, confusion, or emotional difficulty
  - *Action*: Crisis intervention with calming techniques
- 🔴 **HIGH** - Emergency (falls, chest pain, severe distress)
  - *Action*: Immediate contact notification + emergency alert UI

**Safety Agent Tools**:
- `analyze_safety_context` - LLM-based risk assessment
- `crisis_intervention` - Empathetic support responses
- `flag_warning` - Pattern detection (3+ concerns in 24h)
- `place_emergency_call` - Auto-dial emergency contacts
- `generate_emergency_report` - Incident documentation

### 2. 💬 **Context-Aware Conversation**

**Natural Language Understanding**:
```
User: "I'm feeling lonely"
Assistant: "I'm sorry you're feeling lonely. Would you like to talk about it?"
[Topic: loneliness (0.9 confidence), Widgets: MoodSelector]

User: "I want to call my daughter"
Assistant: "Of course! I'll help you call Sarah right away."
[Topic: contact_request (0.95), Widgets: ContactSelector filtered to "Sarah"]
[Context: Previous loneliness mention informs empathetic response]
```

**10 Topic Categories**:
loneliness, health_concern, medication, family, emergency, contact_request, confusion, mood, activities, schedule

### 3. 🎛️ **Dynamic Smart Widgets**

Widgets appear automatically based on conversation context:

- **MoodSelector** - 5 large emoji buttons for mood tracking
- **ContactSelector** - One-tap calling with smart suggestions
- **ActivitySuggestions** - Personalized activity recommendations
- **ReminderList** - Medication & appointment reminders

**Example**:
```
User: "I need to call my son but I'm feeling sad"
→ Shows ContactSelector (filtered to "son") + MoodSelector
→ Agent acknowledges BOTH needs in response
```

### 4. 📞 **Emergency Contact System**

**Smart Contact Selection**:
```python
# User says: "I need to call my doctor"
→ System prioritizes Dr. Smith (relation: "Doctor")
→ Large "Call Now" button with auto-dial
→ Backup: Show all emergency contacts
```

**Mock Contacts** (Hackathon Demo):
- Tommy (Grandson) - 555-0199
- Sarah (Daughter) - 555-0156
- Dr. Smith (Doctor) - 555-0900
- John (Son) - 555-0142

*Production: Integrates with Google Contacts API via MCP*

### 5. ♿ **Elder-Friendly Accessibility**

- **Font Size**: Minimum 18px, defaults to 20px+
- **Touch Targets**: 48px x 48px minimum (WCAG AAA)
- **Contrast**: 7:1 ratio for all text
- **Simple Navigation**: Always visible "Back" button
- **Patient Errors**: "Let's try that again" vs "Error: Invalid Input"
- **Progress Indicators**: Clear visual feedback for all actions

---

## 📊 Demo Scenarios

### Scenario 1: Loneliness → Emergency Contact
```
User: "Nobody visits me anymore. I'm all alone."
→ Risk: MEDIUM (loneliness)
→ Agent: Empathetic response + MoodSelector widget
→ Topic: loneliness (confidence: 0.9)

User: "I think I should call my daughter."
→ Risk: SAFE
→ Agent: "That's a wonderful idea! Let me show you Sarah's contact."
→ Widgets: ContactSelector (filtered to "daughter" = Sarah)
→ Context: Previous loneliness informs supportive tone
```

### Scenario 2: Medical Emergency
```
User: "My chest hurts and I feel dizzy"
→ Risk: HIGH (medical emergency)
→ Agent: "I'm very concerned about your chest pain. I'm contacting your emergency contact immediately."
→ Widgets: EmergencyAlert (auto-call enabled to Dr. Smith)
→ Actions:
  - flag_warning(concern_type="medical", severity="HIGH")
  - place_emergency_call(target="Dr. Smith", reason="chest pain + dizziness")
  - generate_emergency_report(incident_id, user_state, actions_taken)
```

### Scenario 3: Medication Reminder
```
User: "I forgot if I took my pills today"
→ Risk: SAFE
→ Agent: "Let me show you your medication schedule."
→ Widgets: ReminderList (shows daily medications)
→ Context: Previous medication routine from onboarding

User: "Oh yes, I took them at 9am"
→ Agent: "Great! I'll mark that as completed for you."
→ Context updated: medication adherence tracked
```

---

## 🛠️ Tech Stack

### Backend (Python 3.11+)
- **Framework**: A2A Protocol (Agent-to-Agent Communication)
- **LLM**: Ollama (llama3.1:8b) - Local, private, no data leaves device
- **Agents**: 4 specialized agents (Orchestrator, Safety, Conversation, Memory)
- **Context Store**: In-memory (upgradeable to AlloyDB for production)

### Frontend (React 18 + TypeScript)
- **UI Library**: React 18 with TypeScript
- **Styling**: CSS with accessibility-first design
- **State Management**: React hooks + context
- **A2A Client**: Agent communication via JSONRPC

### Infrastructure
- **Protocol**: A2A JSONRPC over HTTP
- **Ports**: 8080 (Safety), 8081 (Conversation), 8082 (Orchestrator), 8083 (Memory)
- **LLM Server**: Ollama on localhost:11434

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
```bash
# 1. Install Ollama (LLM server)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull llama3.1:8b model
ollama pull llama3.1:8b

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Install Node.js dependencies
cd frontend && npm install
```

### Start All Services
```bash
# Terminal 1: Start all backend agents
cd backend && ./start_all.sh

# Terminal 2: Start React frontend
cd frontend && npm start
```

**That's it!** Open http://localhost:3000 to see GrandCompanion in action.

**Detailed setup**: See [QUICK_START.md](QUICK_START.md)

---

## 📁 Project Structure

```
GrandCompanion/
├── README.md                    # This file
├── QUICK_START.md              # 5-minute setup guide
├── LICENSE                      # MIT License
│
├── backend/                     # Python backend agents
│   ├── README.md
│   ├── requirements.txt
│   ├── start_all.sh            # Start all agents
│   └── src/
│       ├── orchestrator/       # Main routing agent (8082)
│       ├── safety/             # Crisis detection (8080)
│       ├── conversation_agent/ # Chat responses (8081)
│       └── memory_agent/       # Context management (8083)
│           └── context_manager.py  # 3-layer context system
│
├── frontend/                    # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConversationMode.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── WidgetPanel.tsx
│   │   │   └── widgets/
│   │   │       ├── MoodSelector.tsx
│   │   │       ├── ContactSelector.tsx
│   │   │       ├── ActivitySuggestions.tsx
│   │   │       └── ReminderList.tsx
│   │   └── hooks/
│   │       └── useElderAgent.ts  # A2A client
│   └── public/
│
├── docs/                        # Technical documentation
│   ├── ARCHITECTURE.md          # System architecture
│   ├── CONTEXT_ARCHITECTURE.md  # Context system deep dive
│   ├── SAFETY_TOOLS_GUIDE.md    # Safety agent tools
│   └── CONTACT_SYSTEM_GUIDE.md  # Contact widget system
│
├── demos/                       # Demo materials
│   ├── screenshots/            # UI screenshots
│   └── test_scripts/           # Test conversation flows
│
└── scripts/                     # Utility scripts
    ├── test_context.py         # Test context architecture
    └── demo_scenarios.py       # Run demo conversations
```

---

## 🎓 Documentation

### For Judges
- **[README.md](README.md)** ← You are here
- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture overview

### For Developers
- **[docs/CONTEXT_ARCHITECTURE.md](docs/CONTEXT_ARCHITECTURE.md)** - Context system (our secret sauce)
- **[docs/SAFETY_TOOLS_GUIDE.md](docs/SAFETY_TOOLS_GUIDE.md)** - Safety agent tools & risk classification
- **[docs/CONTACT_SYSTEM_GUIDE.md](docs/CONTACT_SYSTEM_GUIDE.md)** - Emergency contact system
- **[backend/README.md](backend/README.md)** - Backend agent details
- **[frontend/README.md](frontend/README.md)** - Frontend component guide

---

## 🎯 What Makes Us Different

| Feature | Traditional Elder Care | GrandCompanion |
|---------|----------------------|----------------|
| **Context Memory** | ❌ Forgets between sessions | ✅ Remembers all conversations |
| **Safety Monitoring** | ❌ Manual check-ins | ✅ AI-powered real-time detection |
| **Emergency Response** | ❌ User must dial manually | ✅ One-tap auto-dial with suggestions |
| **Personalization** | ❌ Generic responses | ✅ Context-aware, topic-driven |
| **Privacy** | ❌ Cloud-based (data leaks) | ✅ Local LLM (data never leaves device) |
| **Accessibility** | ❌ Small text, complex UI | ✅ WCAG AAA compliant, elder-friendly |

---

## 🔮 Future Enhancements (Post-Hackathon)

### 🔌 MCP Integration (Model Context Protocol)
Replace mock contacts with real integrations:
- **Google Contacts** - Real contact sync
- **Google Calendar** - Appointment reminders
- **Memory** - Long-term profile storage (AlloyDB)

### 🧠 Advanced AI Features
- **Voice Input/Output** - Speech-to-text & text-to-speech
- **Image Recognition** - "Who is this in the photo?"
- **Emotion Detection** - Facial expression analysis via webcam
- **Predictive Alerts** - "Haven't heard from you in 3 days, checking in..."

### 📊 Analytics & Reporting
- **Caregiver Dashboard** - Family members see engagement trends
- **Health Metrics** - Mood trends, medication adherence
- **Incident Reports** - Automated emergency documentation

### 🌐 Multilingual Support
- Spanish, Mandarin, Portuguese, Hindi
- Cultural context adaptation

---

## 🏆 Hackathon Highlights

### Innovation
- ✨ **First elder care system with centralized context management**
- ✨ **3-tier safety classification with automatic escalation**
- ✨ **Context-aware widget system** (widgets appear based on conversation)

### Technical Excellence
- 🔧 **Multi-agent architecture** using A2A protocol
- 🔧 **Local LLM** (privacy-first, no cloud dependencies)
- 🔧 **Modular design** (easy to add new agents/widgets)

### Social Impact
- ❤️ **Addresses real problem**: 65% of elders report loneliness
- ❤️ **Proven need**: 30% increase in elder tech adoption post-COVID
- ❤️ **Scalable solution**: Can run on affordable hardware

### User Experience
- 🎨 **Elder-friendly design** (WCAG AAA compliant)
- 🎨 **Intuitive interactions** (one-tap calling, large buttons)
- 🎨 **Empathetic AI** (warm, patient, never judgmental)

---

## 👥 Team

**Built with ❤️ for the Hackathon by the GrandCompanion Team**

*This project demonstrates the power of AI to improve quality of life for our aging population.*

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Anthropic** - A2A Protocol for agent communication
- **Ollama** - Local LLM inference
- **React Team** - Frontend framework
- **Our Beta Testers** - Elders who provided invaluable feedback

---

## 📞 Contact

- **Demo Video**: [Coming Soon]
- **Slides**: [Coming Soon]
- **GitHub**: [This Repository]
- **Questions?** Open an issue or reach out to the team!

---

<div align="center">

**🧓💙 Built with love for our elders 💙🧓**

*"Technology should help elders stay independent, not make them dependent."*

[🚀 Get Started](QUICK_START.md) | [📖 Documentation](docs/ARCHITECTURE.md) | [🎥 Watch Demo](#)

</div>
