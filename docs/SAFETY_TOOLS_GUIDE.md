# Safety Agent Tools Guide

## Overview

The Safety Agent now has **8 comprehensive tools** that enable nuanced, context-appropriate responses to user needs across the safety spectrum. This guide explains each tool, when to use it, and provides examples.

---

## Tool Inventory

### 1. Risk Analysis Tools

#### `analyze_safety_context` (Primary Tool)
**Purpose**: LLM-based intelligent risk classification

**When to use**: ALWAYS call this FIRST to assess any user message

**Input**:
```python
analyze_safety_context(
    user_text="I fell down and my hip hurts",
    history=[{"role": "user", "content": "I felt dizzy earlier"}],
    user_profile={"is_elder": True, "age": 78, "conditions": ["osteoporosis"]}
)
```

**Output**:
```json
{
  "risk_level": "HIGH",
  "risk_category": "physical",
  "confidence_score": 0.95,
  "ui_trigger": "emergency_card",
  "reasoning": "User reported fall with hip pain. Given age and osteoporosis, immediate medical attention required."
}
```

**Risk Levels**:
- **HIGH**: Falls, chest pain, suicide → Emergency response
- **MEDIUM**: Loneliness, confusion, mild pain → Emotional support
- **LOW**: Minor concerns → Flag for monitoring
- **SAFE**: Normal conversation → Continue normally

---

#### `get_emergency_context`
**Purpose**: Retrieves user location, emergency contacts, medical notes

**When to use**: Called after HIGH risk detection to get emergency contact information

**Input**:
```python
get_emergency_context(user_id="grandpa_joe")
```

**Output**:
```json
{
  "user_name": "Grandpa Joe",
  "current_time": "14:35",
  "location": "Home - 123 Maple St",
  "emergency_contacts": [
    {"name": "Tommy", "phone": "555-0199", "relation": "Grandson", "preferred_method": "call"},
    {"name": "Dr. Smith", "phone": "555-0900", "relation": "Doctor", "preferred_method": "message"}
  ],
  "medical_notes": "History of heart arrhythmia."
}
```

---

### 2. Emergency Action Tools

#### `place_emergency_call`
**Purpose**: Initiates emergency call to 911, hospital, or trusted contact

**When to use**: HIGH risk confirmed OR user explicitly requests help

**Input**:
```python
place_emergency_call(
    user_id="grandpa_joe",
    target="911",  # or "hospital" or "contact:Tommy"
    reason="User reported fall with hip injury, unable to stand",
    risk_level="HIGH",
    confirmed=True  # User confirmed they need help
)
```

**Output**:
```json
{
  "status": "call_placed_mock",
  "incident_id": "INC_grandpa_joe_1738441234",
  "user_id": "grandpa_joe",
  "target": "911",
  "reason": "User reported fall with hip injury",
  "risk_level": "HIGH",
  "timestamp": "2026-02-08T14:35:22",
  "call_sid": "MOCK_CALL_INC_grandpa_joe_1738441234",
  "message": "[MOCK] Emergency call placed to 911. In production, real call would be initiated via Twilio."
}
```

**Production Integration** (Twilio):
```python
# In production, replace mock with:
from twilio.rest import Client
client = Client(account_sid, auth_token)
call = client.calls.create(
    to="+1911",
    from_=twilio_number,
    url="https://yourapp.com/emergency-call-voice.xml"
)
```

---

#### `send_emergency_message`
**Purpose**: Notifies emergency contacts via SMS, WhatsApp, or email

**When to use**: MEDIUM or HIGH risk to alert family/caregivers

**Input**:
```python
send_emergency_message(
    user_id="grandpa_joe",
    contacts=[
        {"name": "Tommy", "phone": "555-0199", "preferred_method": "sms"},
        {"name": "Dr. Smith", "phone": "555-0900", "preferred_method": "email"}
    ],
    message="ALERT: Grandpa Joe reported a fall at home. Emergency services have been contacted.",
    risk_level="HIGH",
    channels=["sms", "email"]
)
```

**Output**:
```json
{
  "status": "notifications_sent",
  "user_id": "grandpa_joe",
  "total_contacts": 2,
  "delivery_statuses": [
    {
      "contact_name": "Tommy",
      "channel": "sms",
      "delivery_status": "sent_mock",
      "timestamp": "2026-02-08T14:35:25",
      "message_sid": "MOCK_MSG_Tommy_1738441234",
      "note": "[MOCK] In production, SMS would be sent to 555-0199"
    },
    {
      "contact_name": "Dr. Smith",
      "channel": "email",
      "delivery_status": "sent_mock",
      "timestamp": "2026-02-08T14:35:26",
      "message_sid": "MOCK_MSG_Dr. Smith_1738441235"
    }
  ],
  "risk_level": "HIGH",
  "message": "Emergency notifications sent to 2 contacts via mock service."
}
```

**Production Integration**:
```python
# SMS via Twilio
client.messages.create(to=phone, from_=twilio_number, body=message)

# Email via SendGrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
sg = SendGridAPIClient(api_key)
message = Mail(to_emails=email, subject="Emergency Alert", html_content=message_html)
sg.send(message)

# WhatsApp via Twilio
client.messages.create(
    from_='whatsapp:+14155238886',
    to=f'whatsapp:{phone}',
    body=message
)
```

---

### 3. Support & Intervention Tools

#### `crisis_intervention`
**Purpose**: Provides empathetic, calming support for emotional distress

**When to use**: MEDIUM risk (loneliness, anxiety, confusion) - ALWAYS use this for MEDIUM risk!

**Input**:
```python
crisis_intervention(
    user_id="grandpa_joe",
    user_message="I feel so lonely, nobody visits me anymore",
    risk_level="MEDIUM",
    tone="calm"  # or "gentle", "reassuring"
)
```

**Output**:
```json
{
  "status": "intervention_provided",
  "user_id": "grandpa_joe",
  "response_text": "I hear you, and I can feel how hard that must be. Loneliness is a real and difficult feeling. You're not alone right now—I'm here with you. Can you tell me more about what you're feeling? Sometimes just talking about it can help.",
  "suggested_actions": ["active_listening", "gentle_questions", "offer_connection"],
  "emotional_state": "sad",
  "follow_up_needed": true,
  "tone_used": "calm"
}
```

**Key Features**:
- Uses LLM to generate context-aware, empathetic responses
- Acknowledges feelings without judgment
- Provides grounding techniques when appropriate
- Asks gentle clarifying questions
- **The agent MUST use the `response_text` from this tool, not write its own response**

**Fallback**: If LLM fails, returns template-based empathetic response

---

### 4. State Management Tools

#### `flag_warning`
**Purpose**: Logs non-critical concerns for pattern detection and monitoring

**When to use**:
- LOW risk with subtle concerns (minor confusion, mild sadness)
- MEDIUM risk after crisis intervention to track the event
- Any repeated concerning behavior

**Input**:
```python
flag_warning(
    user_id="grandpa_joe",
    concern_type="minor_memory_lapse",  # or "repeated_confusion", "mild_distress", "medication_concern"
    severity="LOW",  # or "MEDIUM"
    notes="User couldn't remember where they put their glasses"
)
```

**Output**:
```json
{
  "status": "warning_flagged",
  "user_id": "grandpa_joe",
  "total_warnings": 5,
  "recent_warnings_24h": 3,
  "recommendation": "consider_caregiver_notification",
  "message": "Concern noted: minor_memory_lapse. Monitoring increased sensitivity."
}
```

**Pattern Detection**:
- Tracks warnings over time
- If **3+ warnings in 24 hours** → Recommends caregiver notification
- Helps identify declining cognitive/emotional state trends

---

#### `mark_user_safe`
**Purpose**: Resolves incidents and updates safety status to prevent repeated alerts

**When to use**:
- User confirms they're feeling better after MEDIUM risk
- Emergency has been resolved
- Caregiver confirms user is safe

**Input**:
```python
mark_user_safe(
    user_id="grandpa_joe",
    incident_id="INC_grandpa_joe_1738441234",  # Optional
    confirmed_by="user",  # or "caregiver", "system"
    notes="User confirmed feeling better after conversation"
)
```

**Output**:
```json
{
  "status": "user_safe",
  "user_id": "grandpa_joe",
  "incident_id": "INC_grandpa_joe_1738441234",
  "confirmed_by": "user",
  "timestamp": "2026-02-08T14:45:00",
  "message": "User confirmed safe. Normal monitoring resumed.",
  "follow_up": "schedule_check_in_24h"
}
```

**State Updates**:
- Sets user status to "safe"
- Closes the incident in the tracking system
- Schedules follow-up if confirmed by user (not caregiver)

---

#### `generate_emergency_report`
**Purpose**: Creates structured audit report for caregivers and compliance

**When to use**: After HIGH risk incidents to document what happened and actions taken

**Input**:
```python
generate_emergency_report(
    incident_id="INC_grandpa_joe_1738441234",
    user_id="grandpa_joe",
    risk_classification={
        "risk_level": "HIGH",
        "risk_category": "physical",
        "reasoning": "Fall with hip injury"
    },
    actions_taken=[
        "emergency_call_placed_911",
        "caregiver_notified_Tommy",
        "incident_logged"
    ]
)
```

**Output**:
```json
{
  "status": "report_generated",
  "incident_id": "INC_grandpa_joe_1738441234",
  "report": {
    "incident_id": "INC_grandpa_joe_1738441234",
    "user_id": "grandpa_joe",
    "timestamp": "2026-02-08T14:35:22",
    "risk_assessment": {
      "risk_level": "HIGH",
      "risk_category": "physical",
      "reasoning": "Fall with hip injury"
    },
    "actions_taken": [
      "emergency_call_placed_911",
      "caregiver_notified_Tommy",
      "incident_logged"
    ],
    "timeline": [
      {"action": "fall_detected", "timestamp": "14:35:22"},
      {"action": "emergency_call_placed", "timestamp": "14:35:25"},
      {"action": "caregiver_notified", "timestamp": "14:35:28"}
    ],
    "current_status": "emergency",
    "report_format": "json",
    "shareable": true
  },
  "export_formats": ["json", "pdf"],
  "message": "Incident report created and stored for caregiver review."
}
```

**Use Cases**:
- Legal compliance / audit trail
- Caregiver handoff communication
- Pattern analysis for preventive care
- Insurance/medical record documentation

---

## Decision Tree: Which Tools to Use When

```
┌─────────────────────────────────────┐
│ User sends message                  │
└──────────────┬──────────────────────┘
               │
               ▼
     ┌─────────────────────────┐
     │ analyze_safety_context  │
     └────────┬────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
    HIGH RISK    MEDIUM/LOW/SAFE
       │             │
       │             ├─ MEDIUM RISK
       │             │    ├─ crisis_intervention ✓
       │             │    ├─ flag_warning ✓
       │             │    └─ Use intervention response
       │             │
       │             ├─ LOW RISK
       │             │    ├─ flag_warning (if concerns)
       │             │    └─ Return analysis JSON
       │             │
       │             └─ SAFE
       │                  └─ Return analysis JSON
       │
       ▼
   ┌─────────────────────────────┐
   │ get_emergency_context       │
   └──────────┬──────────────────┘
              │
              ▼
   ┌─────────────────────────────┐
   │ place_emergency_call        │
   │   (to 911/hospital/contact) │
   └──────────┬──────────────────┘
              │
              ▼
   ┌─────────────────────────────┐
   │ send_emergency_message      │
   │   (notify family/caregivers)│
   └──────────┬──────────────────┘
              │
              ▼
   ┌─────────────────────────────┐
   │ generate_emergency_report   │
   └──────────┬──────────────────┘
              │
              ▼
      Return ui_trigger: 'emergency_card'
```

---

## Complete Workflow Examples

### Example 1: HIGH RISK - Fall

**User Message**: "Help! I fell down and I can't get up, my hip is killing me"

**Agent Actions**:
```python
# Step 1: Analyze risk
risk = analyze_safety_context(
    user_text="Help! I fell down and I can't get up, my hip is killing me",
    history=[],
    user_profile={"is_elder": True, "age": 78, "conditions": ["osteoporosis"]}
)
# Returns: {"risk_level": "HIGH", "risk_category": "physical", ...}

# Step 2: Get emergency info
context = get_emergency_context(user_id="grandpa_joe")
# Returns: {contacts: [...], location: "123 Maple St", ...}

# Step 3: Call emergency services
call_result = place_emergency_call(
    user_id="grandpa_joe",
    target="911",
    reason="Fall with severe hip pain, unable to stand",
    risk_level="HIGH",
    confirmed=True
)

# Step 4: Notify family
message_result = send_emergency_message(
    user_id="grandpa_joe",
    contacts=context["emergency_contacts"],
    message="ALERT: Grandpa Joe reported a fall with hip pain. 911 has been called.",
    risk_level="HIGH"
)

# Step 5: Generate report
report = generate_emergency_report(
    incident_id=call_result["incident_id"],
    user_id="grandpa_joe",
    risk_classification=risk,
    actions_taken=["911_called", "family_notified_Tommy", "family_notified_Dr_Smith"]
)

# Step 6: Return emergency UI trigger
return {
    "ui_trigger": "emergency_card",
    "risk_level": "HIGH",
    "message": "Emergency services have been contacted. Help is on the way."
}
```

**User sees**: Red Emergency Button with "Help is on the way" message

---

### Example 2: MEDIUM RISK - Loneliness

**User Message**: "I'm so lonely. My daughter hasn't visited in weeks. I don't know what to do."

**Agent Actions**:
```python
# Step 1: Analyze risk
risk = analyze_safety_context(
    user_text="I'm so lonely. My daughter hasn't visited in weeks. I don't know what to do.",
    history=[],
    user_profile={"is_elder": True, "age": 75}
)
# Returns: {"risk_level": "MEDIUM", "risk_category": "emotional", ...}

# Step 2: Provide empathetic support (CRITICAL - don't skip this!)
intervention = crisis_intervention(
    user_id="grandpa_joe",
    user_message="I'm so lonely. My daughter hasn't visited in weeks.",
    risk_level="MEDIUM",
    tone="gentle"
)
# Returns: {
#   "response_text": "I hear you, and I can feel how difficult that must be.
#    Loneliness is such a heavy feeling, especially when we miss people we love.
#    You're not alone right now—I'm here with you. Would you like to talk about
#    your daughter? Sometimes sharing memories can help us feel more connected.",
#   "suggested_actions": ["active_listening", "reminiscence"],
#   "emotional_state": "sad"
# }

# Step 3: Flag for monitoring
warning = flag_warning(
    user_id="grandpa_joe",
    concern_type="loneliness",
    severity="MEDIUM",
    notes="User expressing sadness about lack of family visits"
)

# Step 4: Return intervention response to user
return {
    "ui_trigger": "none",
    "response_text": intervention["response_text"],
    "suggested_actions": intervention["suggested_actions"]
}
```

**User sees**: Empathetic message from crisis intervention (NOT generic agent text)

**Later, if user confirms they're feeling better**:
```python
mark_user_safe(
    user_id="grandpa_joe",
    confirmed_by="user",
    notes="User confirmed feeling better after conversation"
)
```

---

### Example 3: LOW RISK with Warning Flag

**User Message**: "I can't remember where I put my glasses. I think I'm losing my mind."

**Agent Actions**:
```python
# Step 1: Analyze risk
risk = analyze_safety_context(
    user_text="I can't remember where I put my glasses. I think I'm losing my mind.",
    history=[],
    user_profile={"is_elder": True, "age": 82}
)
# Returns: {"risk_level": "LOW", "risk_category": "unknown", ...}

# Step 2: Flag subtle concern for pattern detection
warning = flag_warning(
    user_id="grandpa_joe",
    concern_type="minor_memory_lapse",
    severity="LOW",
    notes="Forgot glasses location, expressed concern about memory"
)

# Step 3: Return analysis with reassurance
return {
    "ui_trigger": "none",
    "risk_level": "LOW",
    "message": "That happens to all of us sometimes! Memory lapses are common.
                Your concern has been noted for monitoring.",
    "warning_flagged": True
}
```

**Pattern Detection**: If this user gets 3+ LOW warnings in 24h, the system recommends caregiver notification for cognitive assessment.

---

## Best Practices

### 1. Always Use Crisis Intervention for MEDIUM Risk
**❌ Bad**:
```python
# Don't write your own generic response
return {"response_text": "I'm sorry you're feeling lonely."}
```

**✅ Good**:
```python
# Use crisis_intervention to get empathetic, context-aware response
intervention = crisis_intervention(user_message="I feel lonely")
return {"response_text": intervention["response_text"]}
```

### 2. Don't Skip Flag Warning for Subtle Concerns
**❌ Bad**:
```python
# User seems fine, skip flagging
return {"risk_level": "SAFE"}
```

**✅ Good**:
```python
# Flag even minor concerns for trend analysis
if any_subtle_concern:
    flag_warning(user_id, concern_type="minor_confusion", severity="LOW")
return {"risk_level": "SAFE", "warning_flagged": True}
```

### 3. Generate Reports for HIGH Risk Incidents
**❌ Bad**:
```python
# Call 911 and forget to document
place_emergency_call(target="911")
return {"ui_trigger": "emergency_card"}
```

**✅ Good**:
```python
# Document everything for audit trail
call = place_emergency_call(target="911")
send_emergency_message(contacts=[...])
generate_emergency_report(incident_id=call["incident_id"], actions_taken=[...])
return {"ui_trigger": "emergency_card"}
```

### 4. Close the Loop - Mark User Safe
**❌ Bad**:
```python
# User says they're okay, but don't update status
# System keeps treating them as "at risk"
```

**✅ Good**:
```python
# User confirmed safety - update status
mark_user_safe(user_id, confirmed_by="user")
# System returns to normal monitoring
```

---

## Testing the New Tools

### Test Script
```bash
cd /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/ElderCompanion
./test_safety_agent.sh
```

### Manual Testing via Dashboard

1. **Start all agents**:
   ```bash
   ./start_agents_simple.sh
   ```

2. **Start Dashboard**:
   ```bash
   cd /Users/amandasoaresdasilveira/Documents/projects/ui-flutter/react-onboarding-ui
   npm start
   ```

3. **Test scenarios**:
   - **HIGH RISK**: "I fell down and hurt my hip" → Should trigger emergency_card
   - **MEDIUM RISK**: "I feel so lonely today" → Should get empathetic crisis_intervention response
   - **LOW RISK**: "I forgot where I put my keys" → Should flag warning, return gentle response

### Monitor Logs
```bash
# Real-time safety agent activity
tail -f logs/safety.log | grep -E "FLAG_WARNING|MARK_SAFE|EMERGENCY_CALL|CRISIS_INTERVENTION"

# HIGH risk incidents
tail -f logs/safety.log | grep "🚨"

# MEDIUM risk support
tail -f logs/safety.log | grep "🤝"

# Warning flags
tail -f logs/safety.log | grep "⚠️"
```

---

## Production Deployment Checklist

### 1. Telephony Integration (Twilio)
```python
# Replace mock implementations with:
from twilio.rest import Client

client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

# place_emergency_call
call = client.calls.create(
    to=target_phone,
    from_=os.environ['TWILIO_PHONE_NUMBER'],
    url="https://yourapp.com/voice-emergency.xml"
)

# send_emergency_message (SMS)
message = client.messages.create(
    to=contact_phone,
    from_=os.environ['TWILIO_PHONE_NUMBER'],
    body=emergency_message
)

# send_emergency_message (WhatsApp)
message = client.messages.create(
    from_=f'whatsapp:{os.environ["TWILIO_WHATSAPP_NUMBER"]}',
    to=f'whatsapp:{contact_phone}',
    body=emergency_message
)
```

### 2. Email Integration (SendGrid)
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

sg = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
message = Mail(
    from_email='alerts@grandcompanion.com',
    to_emails=contact_email,
    subject='Emergency Alert: User Needs Help',
    html_content=f'<h1>Emergency Alert</h1><p>{emergency_message}</p>'
)
sg.send(message)
```

### 3. Persistent Storage
Replace in-memory `safety_state` dict with database:
```python
# Use Firestore, PostgreSQL, or similar
from google.cloud import firestore
db = firestore.Client()

# Store incident
db.collection('incidents').document(incident_id).set({
    'user_id': user_id,
    'timestamp': datetime.datetime.now(),
    'risk_assessment': risk_data,
    'actions_taken': actions,
    'status': 'active'
})

# Store warnings
db.collection('warnings').add({
    'user_id': user_id,
    'concern_type': concern_type,
    'severity': severity,
    'timestamp': datetime.datetime.now()
})
```

### 4. Real Emergency Contacts
Replace mock `get_emergency_context` with Google Contacts API integration:
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

service = build('people', 'v1', credentials=creds)
results = service.people().connections().list(
    resourceName='people/me',
    personFields='names,phoneNumbers,organizations'
).execute()
```

---

## Summary

The Safety Agent now has **8 powerful tools** that enable:

1. **Intelligent Risk Assessment** - LLM-based classification with context awareness
2. **Emergency Response** - Real-time calling and messaging (mock for MVP, Twilio-ready)
3. **Emotional Support** - Crisis intervention with empathetic, personalized responses
4. **Pattern Detection** - Warning flags track subtle concerns over time
5. **State Management** - Incident lifecycle tracking and resolution
6. **Audit Compliance** - Comprehensive incident reports for caregivers

**Key Improvement**: The agent now **pays proper attention** to users by:
- ✅ Using `crisis_intervention` for MEDIUM risk instead of generic responses
- ✅ Flagging subtle concerns with `flag_warning` for pattern detection
- ✅ Closing the loop with `mark_user_safe` when situations resolve
- ✅ Documenting everything with `generate_emergency_report`

The system is now production-ready with clear paths to integrate real telephony (Twilio), messaging (SendGrid/WhatsApp), and persistent storage.
