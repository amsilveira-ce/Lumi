# Context Architecture - Single Source of Truth

## 🎯 Problem Solved

**BEFORE**: System lost conversational continuity because context was fragmented across agents. Agents operated in isolation without shared state.

**AFTER**: Centralized Context Manager provides single source of truth. All agents receive full context before processing.

---

## 🏗️ Three-Layer Context Structure

```
┌─────────────────────────────────────────────────────────┐
│              CONTEXT MANAGER (Port 8083)                │
│           Single Source of Truth for Context            │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    LAYER 1          LAYER 2          LAYER 3
Conversation       Active Topics     User Context
   Context
```

### Layer 1: Conversation Context
```json
{
  "conversation_history": [
    {
      "role": "user",
      "content": "I need to call my son",
      "timestamp": "2025-01-15T10:30:00"
    },
    {
      "role": "assistant",
      "content": "Of course! I'll help you call your son right away.",
      "timestamp": "2025-01-15T10:30:05"
    }
  ]
}
```
- Last 10 turns with timestamps
- Enables continuity ("you said earlier...", "as we discussed...")
- Used by Conversation Agent for context-aware responses

### Layer 2: Active Topic Context
```json
{
  "active_topics": {
    "primary": {
      "topic": "contact_request",
      "confidence": 0.9,
      "started_at": "2025-01-15T10:30:00",
      "keywords": ["call", "son", "contact"]
    },
    "secondary": [
      {
        "topic": "loneliness",
        "confidence": 0.6,
        "started_at": "2025-01-15T10:28:00"
      }
    ]
  }
}
```
- Primary topic: Highest confidence (what conversation is about NOW)
- Secondary topics: Related themes (background context)
- Auto-detected using keyword matching (10 topics supported)
- Used for context-aware widget selection

**Supported Topics**:
1. `loneliness` - User expressing isolation
2. `health_concern` - Pain, symptoms, feeling unwell
3. `medication` - Medication reminders, prescriptions
4. `family` - Family mentions, relationships
5. `emergency` - Falls, urgent help needed
6. `contact_request` - Wanting to call/reach someone
7. `confusion` - Memory issues, disorientation
8. `mood` - Emotional expressions
9. `activities` - Boredom, wanting to do something
10. `schedule` - Appointments, reminders

### Layer 3: User Context
```json
{
  "user_profile": {
    "age": 78,
    "is_elder": true,
    "conditions": ["heart arrhythmia"],
    "emergency_contacts": [
      {
        "id": "1",
        "name": "John Smith",
        "relation": "Son",
        "phone": "+1-555-0142"
      }
    ],
    "preferences": {
      "tone": "warm",
      "pace": "slow",
      "cognitive_comfort": "intermediate"
    }
  },
  "current_state": {
    "emotional_state": "calm",
    "safety_status": "safe",
    "cognitive_clarity": "clear",
    "engagement_level": "active",
    "last_updated": "2025-01-15T10:30:05"
  }
}
```
- **Profile**: Demographics, conditions, contacts, preferences
- **Current State**: Real-time emotional/safety/cognitive tracking
- Updated by Safety Agent after risk assessment
- Used for personalized responses and emergency handling

---

## 🚨 CRITICAL RULE

**NO AGENT MAY BE INVOKED WITHOUT FULL CONTEXT PACKAGE**

### Before Context Architecture ❌
```python
# OLD WAY (Context fragmented, agents blind)
safety_result = check_safety(message)  # No context!
response = conversation_agent(message)  # No context!
```

### After Context Architecture ✅
```python
# NEW WAY (Context-first, all agents informed)
# STEP 1: Fetch context (ALWAYS FIRST)
full_context = memory_agent.get_context(user_id)

# STEP 2: Pass context to ALL agents
safety_result = check_safety(message, user_id, full_context)
response = conversation_agent(message, full_context)
widgets = determine_widgets(message, full_context)

# STEP 3: Update context with new turn
memory_agent.update_turn(user_id, message, response)
```

---

## 📡 Agent Flow (Orchestrator)

```
┌─────────────────────────────────────────────────────────┐
│  1. User sends message                                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  2. ORCHESTRATOR: Fetch full context from Memory Agent  │
│     Action: get_context                                  │
│     Returns: {conversation, topics, profile, state}      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  3. SAFETY AGENT: Check with context                    │
│     Input: message + full_context                        │
│     Output: {is_safe, risk_level, reason}               │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      HIGH RISK               SAFE
            │                     │
            ▼                     ▼
┌────────────────────┐  ┌────────────────────┐
│ 4a. EMERGENCY      │  │ 4b. CONVERSATION   │
│     - Alert UI     │  │     - Generate     │
│     - Call contact │  │       response     │
│     - Update state │  │     - Select       │
│                    │  │       widgets      │
└────────────────────┘  └────────────────────┘
            │                     │
            └──────────┬──────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  5. MEMORY AGENT: Update context with new turn          │
│     Action: update_turn                                  │
│     Data: {user_message, assistant_message,              │
│            risk_assessment (if emergency)}               │
│     Side effects:                                        │
│     - Adds to conversation_history (max 10 turns)       │
│     - Updates active_topics (primary/secondary)          │
│     - Updates current_state (emotional/safety/cognitive) │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Context Operations (API)

### 1. `get_context` (MOST IMPORTANT)
**When**: Before ANY agent invocation (CRITICAL!)
**Input**:
```json
{
  "action": "get_context",
  "user_id": "user123"
}
```
**Output**: Full context package (all 3 layers)

### 2. `update_turn`
**When**: After each user-agent exchange
**Input**:
```json
{
  "action": "update_turn",
  "user_id": "user123",
  "user_message": "I need to call my son",
  "assistant_message": "Of course! I'll help you...",
  "risk_assessment": {
    "risk_level": "SAFE",
    "risk_category": "contact_request"
  }
}
```
**Side Effects**:
- Adds turn to history (keeps last 10)
- Detects and updates active topics
- Updates user state based on risk assessment

### 3. `update_state`
**When**: Agent needs to update user state independently
**Input**:
```json
{
  "action": "update_state",
  "user_id": "user123",
  "emotional_state": "anxious",
  "safety_status": "monitoring"
}
```

### 4. `get_history`
**When**: Need only conversation history (lightweight)
**Input**:
```json
{
  "action": "get_history",
  "user_id": "user123"
}
```
**Output**: Last 10 conversation turns

### 5. `update_profile`
**When**: Profile data changes (e.g., after onboarding)
**Input**:
```json
{
  "action": "update_profile",
  "user_id": "user123",
  "profile": {
    "emergency_contacts": [...],
    "age": 78,
    "conditions": ["heart arrhythmia"]
  }
}
```

---

## 📝 Code Examples

### Example 1: Context-Aware Safety Check
```python
# Orchestrator fetches context first
full_context = await get_full_context(user_id)

# Safety Agent receives conversation history to detect patterns
safety_payload = {
    "message": "I feel dizzy",
    "user_id": user_id,
    "conversation_history": full_context["conversation_history"][-5:],
    "current_state": full_context["current_state"],
    "active_topics": full_context["active_topics"]
}

# Safety Agent can now detect:
# - User mentioned dizziness 3 times today (pattern!)
# - User's emotional state is already "anxious"
# - Active topic is "health_concern"
# => Escalate to MEDIUM risk, show ContactSelector for doctor
```

### Example 2: Context-Aware Widget Selection
```python
# Without context (OLD)
if "call" in message:
    show_contact_widget()  # Generic

# With context (NEW)
if "call" in message:
    primary_topic = full_context["active_topics"]["primary"]["topic"]

    if primary_topic == "emergency":
        # Emergency context: Show emergency contacts + auto-dial
        show_contact_widget(emergency_mode=True, auto_dial=True)
    elif primary_topic == "family":
        # Family context: Prioritize family contacts
        show_contact_widget(filter="family")
    else:
        # General: Show all contacts
        show_contact_widget()
```

### Example 3: Continuity Across Turns
```
Turn 1:
User: "I'm feeling lonely today"
Assistant: "I'm sorry you're feeling lonely. Would you like to talk about it?"
[Topics updated: primary=loneliness (0.9)]

Turn 2:
User: "Maybe I should call my daughter"
Assistant: "That's a wonderful idea! Connecting with your daughter can help with loneliness. Let me show you her contact."
[Topics: primary=contact_request (0.95), secondary=loneliness (0.6)]
[Widget: ContactSelector shown, filtered to "daughter"]

Turn 3:
User: "What was her number again?"
Assistant: "I have her saved as Sarah at 555-0156. Would you like me to help you call her?"
[Context used: previous turn mentioned daughter, profile has emergency contact "Sarah"]
```

---

## 🔄 Topic Detection Algorithm

```python
def _detect_topics(user_message: str, assistant_message: str) -> list:
    """
    Detects topics using keyword matching.
    Returns: [(topic, confidence), ...]
    """
    topics = []
    text = (user_message + " " + assistant_message).lower()

    # Example: loneliness detection
    loneliness_keywords = ["lonely", "alone", "nobody", "isolated", "miss", "visits"]
    matches = sum(1 for kw in loneliness_keywords if kw in text)

    if matches > 0:
        confidence = min(1.0, matches / len(loneliness_keywords) * 2)
        topics.append(("loneliness", confidence))

    # Sort by confidence, return top 3
    topics.sort(key=lambda x: x[1], reverse=True)
    return topics[:3]
```

**Topic Update Logic**:
- **Primary topic**: Highest confidence topic becomes primary
- **Secondary topics**: Next 2 highest confidence topics
- **Threshold**: Minimum 1 keyword match required

---

## 🧪 Testing the Architecture

### Test 1: Context Continuity
```bash
# Turn 1
curl -X POST http://localhost:8082/api/chat \
  -d '{"user_id": "test", "message": "I feel sad"}'
# Expected: MoodSelector widget shown, topic=mood

# Turn 2
curl -X POST http://localhost:8082/api/chat \
  -d '{"user_id": "test", "message": "I want to talk to someone"}'
# Expected: ContactSelector shown
# Response references "feeling sad" from Turn 1 (continuity!)
```

### Test 2: Safety with Context
```bash
# Turn 1
curl -X POST http://localhost:8082/api/chat \
  -d '{"user_id": "test", "message": "My chest hurts a bit"}'
# Expected: MEDIUM risk, topic=health_concern

# Turn 2
curl -X POST http://localhost:8082/api/chat \
  -d '{"user_id": "test", "message": "The pain is getting worse"}'
# Expected: HIGH risk (pattern detected across turns!)
# Emergency alert triggered
```

### Test 3: Topic-Aware Widgets
```bash
curl -X POST http://localhost:8082/api/chat \
  -d '{"user_id": "test", "message": "I need to call my son but I am feeling very lonely"}'
# Expected:
# - Primary topic: contact_request (0.9)
# - Secondary topic: loneliness (0.6)
# - Widgets: ContactSelector + MoodSelector
# - Response acknowledges BOTH topics
```

---

## 📊 Benefits Achieved

### 1. **Conversational Continuity** ✅
- System remembers what was discussed
- Responses reference previous context
- Topics persist across turns

### 2. **Pattern Detection** ✅
- Safety Agent detects repeated distress
- Topic tracking shows conversation evolution
- State changes tracked over time

### 3. **Context-Aware Responses** ✅
- Widgets shown based on topic + message
- Emergency contacts prioritized by relation
- Response tone adapts to user state

### 4. **Single Source of Truth** ✅
- All agents read from same context
- No conflicting information
- Consistent user state across system

### 5. **Backward Compatibility** ✅
- Legacy `store` → `update_turn` conversion
- Legacy `retrieve` → `get_history` conversion
- Existing code continues to work

---

## 🔐 Security & Privacy

### Data Lifetime
- Context stored in-memory (deleted on restart)
- Production: Migrate to AlloyDB with encryption
- Conversation history: Max 10 turns (auto-pruned)

### Access Control
- Context scoped by `user_id`
- No cross-user access possible
- Agent-to-agent communication via A2A protocol only

---

## 🚀 Production Upgrade Path

### Current (MVP)
- In-memory storage
- Keyword-based topic detection
- Simple state management

### Future
1. **Persistent Storage**: AlloyDB for context
2. **LLM-Based Topics**: Replace keywords with LLM analysis
3. **Vector Search**: Semantic memory retrieval
4. **Advanced State**: ML-based state prediction
5. **Analytics**: Topic trends, engagement metrics

---

## 📚 Related Documentation

- [SAFETY_TOOLS_GUIDE.md](./SAFETY_TOOLS_GUIDE.md) - Safety Agent tools
- [CONTACT_SYSTEM_GUIDE.md](./CONTACT_SYSTEM_GUIDE.md) - Contact widget system
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Overall system architecture

---

## 🆘 Troubleshooting

### Problem: Context not persisting
**Cause**: Memory Agent not running
**Fix**: Start Memory Agent on port 8083
```bash
cd ElderCompanion/src/memory_agent
python server.py
```

### Problem: Agents ignore context
**Cause**: Orchestrator not fetching context first
**Fix**: Verify Orchestrator calls `get_context` before routing

### Problem: Topics not detected
**Cause**: Keywords not matching
**Fix**: Check topic_keywords mapping in context_manager.py
