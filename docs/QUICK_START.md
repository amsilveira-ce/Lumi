# GrandCompanion Quick Start Guide

## ✅ System Status

**All Agents Running:**
- ✅ Orchestrator (Main Entry): http://localhost:8082
- ✅ Safety Agent: http://localhost:8080
- ✅ Conversation Agent: http://localhost:8081
- ✅ Memory Agent: http://localhost:8083

**Dashboard:**
- ✅ React App: http://localhost:3000

---

## 🚀 Quick Start

### 1. Start All Agents (Already Running!)
```bash
cd /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/ElderCompanion
./start_agents_simple.sh
```

### 2. Start Dashboard
```bash
cd /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/react-onboarding-ui
npm start
```

### 3. Open in Browser
http://localhost:3000

---

## 🎯 How It Works

### User Flow:
1. **Dashboard loads** → Shows GrandCompanion home screen
2. **User speaks/types** → "I'm feeling sad today"
3. **Dashboard sends** → Orchestrator (port 8082)
4. **Orchestrator checks** → Safety Agent: "Is this safe?"
5. **Safety Agent replies** → "Safe - no crisis detected"
6. **Orchestrator routes** → Conversation Agent for response
7. **Orchestrator analyzes** → "User mentioned feelings → show MoodSelector"
8. **Dashboard receives**:
   ```json
   {
     "text": "I'm sorry you're feeling sad. Would you like to talk about it?",
     "ui_commands": [{
       "action": "show",
       "component": "MoodSelector",
       "props": {...}
     }]
   }
   ```
9. **MoodSelector appears** on screen!

### Emergency Flow:
1. User says: **"I fell down and can't get up"**
2. Safety Agent detects: **HIGH RISK**
3. Orchestrator triggers: **EmergencyAlert UI**
4. Dashboard shows: **Red emergency screen with auto-call**

---

## 📡 API Examples

### Send Message from Dashboard
```javascript
const response = await sendAction('conversation', {
  message: "I'm feeling sad",
  user_id: "grandpa_joe",
  elder_profile: {
    cognitive_comfort: 'intermediate',
    emergency_contacts: [...]
  }
});

// Response:
// {
//   text: "I'm sorry to hear that...",
//   ui_commands: [{action: "show", component: "MoodSelector", ...}]
// }
```

### Test with cURL
```bash
# Test Orchestrator
curl -X POST http://localhost:8082/message \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"action\": \"conversation\", \"message\": \"Hello\", \"user_id\": \"test\"}"}'
```

---

## 🔍 Debugging

### Check Logs
```bash
# All logs
tail -f /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/ElderCompanion/logs/*.log

# Individual agents
tail -f logs/orchestrator.log
tail -f logs/safety.log
tail -f logs/conversation.log
tail -f logs/memory.log
```

### Check Agent Health
```bash
# See all running agents
ps aux | grep "python.*server.py"

# Test individual agents
curl http://localhost:8080  # Safety
curl http://localhost:8081  # Conversation
curl http://localhost:8082  # Orchestrator
curl http://localhost:8083  # Memory
```

### Stop All Agents
```bash
lsof -ti:8080,8081,8082,8083 | xargs kill -9
```

---

## 🎨 Dashboard Features

### Adaptive UI
The Dashboard automatically adjusts based on user preferences:
- **Text Size**: Normal → Large → Extra-Large
- **Contrast**: Normal → High (black borders, no shadows)
- **Button Size**: 48px → 64px → 80px

### Available Widgets
1. **MoodSelector** - Triggered by: "feel", "sad", "happy", "anxious"
2. **ActivitySuggestions** - Triggered by: "bored", "nothing to do"
3. **ReminderList** - Triggered by: "medication", "doctor", "appointment"

### Navigation
- **Onboarding Mode**: Complete elder-specific setup
- **Dashboard Mode**: Home screen with health, social, schedule
- **Conversation Mode**: Chat interface with dynamic widgets

Use the **🔄 Switch Mode** button (top-right) to cycle through modes.

---

## 🧪 Testing Scenarios

### Test 1: Normal Conversation
1. Open Dashboard
2. Click voice button or type: **"Hello, how are you?"**
3. Expect: Warm greeting from Conversation Agent
4. No widgets shown (no triggers)

### Test 2: Mood Trigger
1. Type: **"I'm feeling really sad today"**
2. Expect:
   - Empathetic response
   - MoodSelector widget appears
3. Click a mood in the selector
4. Check console logs for selection

### Test 3: Activity Suggestions
1. Type: **"I'm bored, I don't know what to do"**
2. Expect:
   - Encouraging response
   - ActivitySuggestions widget appears with 4 options

### Test 4: Reminder List
1. Type: **"I need to remember to take my medication"**
2. Expect:
   - Supportive response
   - ReminderList widget appears with mock reminders

### Test 5: Emergency Detection (CRITICAL)
1. Type: **"Help! I fell down and can't get up"**
2. Expect:
   - **Immediate red alert screen**
   - **Emergency contact information displayed**
   - **Auto-call initiated (simulated)**
   - Check Safety Agent logs for crisis detection

### Test 6: Voice Input
1. Click the **blue microphone button**
2. Watch it pulse (listening state)
3. Check console for "Voice input toggled"
4. In production, would capture actual speech

---

## 🔧 Configuration

### Agent URLs (in Orchestrator)
```python
SAFETY_AGENT_URL = "http://localhost:8080"
CONVERSATION_AGENT_URL = "http://localhost:8081"
MEMORY_AGENT_URL = "http://localhost:8083"
```

### LLM Configuration
```python
# Safety Agent (src/safety/server.py)
model = "ollama_chat/gpt-oss:20b"  # Line 114

# Conversation Agent (src/conversation_agent/server.py)
model = "llama3.1:8b"  # Line 86
base_url = "http://localhost:11434"  # Line 87
```

### Dashboard API URL
```typescript
// react-onboarding-ui/src/hooks/useOnboardingAgent.ts
const agentUrl = 'http://localhost:8082'  // Line 141
```

---

## 🎯 Next Steps

1. **Test Emergency Flow**: Type "I fell" and observe Safety Agent
2. **Test Widgets**: Try different phrases to trigger each widget
3. **Check Memory**: Send multiple messages, see if context is retained
4. **Customize Responses**: Edit Conversation Agent prompts in `src/conversation_agent/server.py:78-84`
5. **Add New Widgets**: Create new widget components and update Orchestrator's `determine_widgets()`

---

## 📚 Key Files

### Backend (Python)
- **Orchestrator**: `src/orchestrator/server.py` (Main entry, routing logic)
- **Safety**: `src/safety/server.py` (Crisis detection with ADK)
- **Conversation**: `src/conversation_agent/server.py` (Warm responses via Ollama)
- **Memory**: `src/memory_agent/server.py` (Context storage/retrieval)

### Frontend (React/TypeScript)
- **Dashboard**: `src/components/Dashboard.tsx` (Home screen)
- **ConversationMode**: `src/components/ConversationMode.tsx` (Chat interface)
- **Widgets**: `src/components/widgets/*` (MoodSelector, ActivitySuggestions, ReminderList)
- **Preferences Hook**: `src/hooks/useUserPreferences.ts` (Adaptive UI logic)

---

## 🐛 Common Issues

### "Connection refused" error
- **Cause**: Agents not running
- **Fix**: `./start_agents_simple.sh`

### Agents crash on startup
- **Check**: `tail -f logs/orchestrator.log`
- **Common**: Missing dependencies → `pip install uvicorn a2a-sdk google-genai-adk litellm httpx`

### Widgets don't appear
- **Check**: Console logs in browser (F12)
- **Verify**: Orchestrator's `determine_widgets()` logic
- **Test**: Direct message to Orchestrator with cURL

### Dashboard shows blank screen
- **Check**: React compilation errors
- **Verify**: All imports working (`lucide-react`, `tailwindcss`)
- **Fix**: `npm install`

---

## 📞 Support

Check logs for detailed error messages:
```bash
tail -100 logs/orchestrator.log | grep ERROR
```

For architecture questions, see:
- **README.md** - Full system documentation
- **Agent files** - Inline comments explain each component

---

**Happy Testing! 🎉**

Your GrandCompanion multi-agent system is ready to provide compassionate care!
