import logging
import uvicorn
import json
import os
import asyncio
import datetime
import litellm
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import new_task, completed_task, new_artifact, new_agent_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Part,
    TextPart,
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
    UnsupportedOperationError,
)
from a2a.server.tasks import TaskUpdater
from a2a.utils.errors import ServerError
from google.genai import types as genai_types
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SafetyAgent")

# ==========================================
# 1. TOOL: Context Retrieval
# ==========================================

def get_emergency_context(user_id: str) -> dict:
    """
    Retrieves static context about the user (Location, Contacts).
    Does NOT assess risk.
    """
    return {
        "user_name": "Grandpa Joe",
        "current_time": datetime.datetime.now().strftime("%H:%M"),
        "location": "Home - 123 Maple St",
        "emergency_contacts": [
            {"name": "Tommy", "phone": "555-0199", "relation": "Grandson", "preferred_method": "call"},
            {"name": "Dr. Smith", "phone": "555-0900", "relation": "Doctor", "preferred_method": "message"}
        ],
        "medical_notes": "History of heart arrhythmia."
    }


# ==========================================
# 2. TOOL: LLM-Based Safety Analysis
# ==========================================

def analyze_safety_context(
    user_text: str,
    history: list = None,
    user_profile: dict = None
) -> dict:
    """
    Analyzes user input using LLM for intelligent risk classification.

    This function uses an LLM to detect medical emergencies, emotional distress,
    physical danger, and mental health crises. It replaces simple keyword matching
    with contextual understanding.

    Args:
        user_text (str): The current message from the user.
        history (list): Last 5 conversation turns in format [{"role": "user|assistant", "content": "..."}].
        user_profile (dict): User context containing:
            - is_elder (bool): Whether the user is elderly
            - conditions (list): Medical conditions (e.g., ["heart arrhythmia", "diabetes"])
            - age (int): User's age

    Returns:
        dict: Structured risk assessment containing:
            - risk_level (str): "SAFE" | "LOW" | "MEDIUM" | "HIGH"
            - risk_category (str): "medical" | "emotional" | "physical" | "unknown"
            - confidence_score (float): 0.0 to 1.0
            - ui_trigger (str): "emergency_card" (ONLY if HIGH risk) | "none"
            - reasoning (str): Brief explanation of the classification
    """
    logger.info(f"🛡️ [SAFETY_CONTEXT] Analyzing: {user_text}")

    # Handle default values
    if history is None:
        history = []
    if user_profile is None:
        user_profile = {"is_elder": True, "conditions": [], "age": 75}

    # Build context for LLM
    conversation_context = "\n".join([
        f"{turn.get('role', 'user')}: {turn.get('content', '')}"
        for turn in history[-5:]  # Last 5 turns only
    ])

    medical_conditions = ", ".join(user_profile.get("conditions", ["none reported"]))

    # LLM Prompt for Risk Classification
    classification_prompt = f"""You are a medical safety classification system. Analyze the following message for risk level.

USER PROFILE:
- Age: {user_profile.get('age', 'unknown')}
- Is Elder: {user_profile.get('is_elder', False)}
- Medical Conditions: {medical_conditions}

RECENT CONVERSATION:
{conversation_context if conversation_context else "(No prior conversation)"}

CURRENT MESSAGE:
"{user_text}"

TASK: Classify the risk level based on these criteria:

HIGH RISK (Immediate danger requiring emergency response):
- Physical injury: falls, bleeding, severe pain, broken bones
- Medical emergencies: chest pain, difficulty breathing, stroke symptoms, heart attack
- Mental health crisis: suicide ideation, self-harm, severe panic attack
- Inability to perform critical functions: can't move, trapped, unconscious

MEDIUM RISK (Emotional distress or confusion requiring support):
- Moderate emotional distress: sadness, loneliness, anxiety, grief
- Cognitive confusion: disorientation, memory problems, not recognizing surroundings
- Minor health concerns: headache, mild pain, fatigue
- Medication concerns: forgot to take medication, unsure about dosage

LOW RISK (Normal conversation):
- General conversation: greetings, weather, hobbies, reminiscing
- Minor questions: asking about time, schedule, activities
- Positive expressions: happiness, gratitude, excitement

SAFE:
- Completely normal, casual conversation with no risk indicators

OUTPUT FORMAT (JSON only):
{{
  "risk_level": "SAFE" | "LOW" | "MEDIUM" | "HIGH",
  "risk_category": "medical" | "emotional" | "physical" | "unknown",
  "confidence_score": 0.0-1.0,
  "ui_trigger": "emergency_card" (ONLY if HIGH) | "none",
  "reasoning": "Brief 1-2 sentence explanation"
}}

Respond ONLY with valid JSON. No additional text."""

    try:
        # Use LiteLLM to call Gemini
        model_name = os.environ.get("SAFETY_CLASSIFIER_MODEL", "gemini/gemini-2.0-flash-exp")

        # Set litellm timeout to 15 seconds to prevent hanging
        litellm.set_verbose = False  # Reduce log noise

        response = litellm.completion(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a medical safety classifier. Respond ONLY with valid JSON."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=300,
            timeout=15.0,  # 15 second timeout
            drop_params=True  # Drop unsupported parameters instead of erroring
        )

        # Extract JSON from response
        llm_output = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if llm_output.startswith("```json"):
            llm_output = llm_output[7:]
        if llm_output.startswith("```"):
            llm_output = llm_output[3:]
        if llm_output.endswith("```"):
            llm_output = llm_output[:-3]
        llm_output = llm_output.strip()

        # Parse JSON
        result = json.loads(llm_output)

        # Validate required fields
        required_fields = ["risk_level", "risk_category", "confidence_score", "ui_trigger", "reasoning"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Ensure ui_trigger is "emergency_card" ONLY for HIGH risk
        if result["risk_level"] == "HIGH":
            result["ui_trigger"] = "emergency_card"
        else:
            result["ui_trigger"] = "none"

        # Log HIGH risk detections
        if result["risk_level"] == "HIGH":
            logger.warning(f"🚨 [SAFETY_CONTEXT] HIGH RISK DETECTED: {result['reasoning']}")
        elif result["risk_level"] == "MEDIUM":
            logger.info(f"⚠️ [SAFETY_CONTEXT] MEDIUM RISK: {result['reasoning']}")
        else:
            logger.info(f"✅ [SAFETY_CONTEXT] {result['risk_level']}: {result['reasoning']}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"❌ [SAFETY_CONTEXT] Failed to parse LLM JSON: {e}")
        logger.error(f"Raw LLM output: {llm_output}")
        # Fallback to keyword matching
        return _fallback_keyword_analysis(user_text)

    except Exception as e:
        logger.error(f"❌ [SAFETY_CONTEXT] LLM analysis failed: {e}", exc_info=True)
        # Fallback to keyword matching
        return _fallback_keyword_analysis(user_text)


def _fallback_keyword_analysis(text: str) -> dict:
    """
    Fallback keyword-based analysis if LLM fails.
    Used as a safety net to ensure the system never fails completely.
    """
    logger.warning("⚠️ [SAFETY_CONTEXT] Using fallback keyword analysis")

    crisis_keywords = {
        "high": ["fall", "fell", "chest pain", "heart attack", "stroke", "bleeding", "suicide", "kill myself", "can't breathe", "unconscious"],
        "medium": ["sad", "lonely", "anxious", "confused", "dizzy", "headache", "forgot medication"],
    }

    text_lower = text.lower()

    # Check HIGH risk keywords
    for keyword in crisis_keywords["high"]:
        if keyword in text_lower:
            return {
                "risk_level": "HIGH",
                "risk_category": "medical" if keyword in ["chest pain", "heart attack", "stroke", "bleeding"] else "physical",
                "confidence_score": 0.7,
                "ui_trigger": "emergency_card",
                "reasoning": f"Fallback detection: keyword '{keyword}' indicates potential crisis"
            }

    # Check MEDIUM risk keywords
    for keyword in crisis_keywords["medium"]:
        if keyword in text_lower:
            return {
                "risk_level": "MEDIUM",
                "risk_category": "emotional" if keyword in ["sad", "lonely", "anxious"] else "medical",
                "confidence_score": 0.6,
                "ui_trigger": "none",
                "reasoning": f"Fallback detection: keyword '{keyword}' suggests moderate concern"
            }

    # Default to SAFE
    return {
        "risk_level": "SAFE",
        "risk_category": "unknown",
        "confidence_score": 0.5,
        "ui_trigger": "none",
        "reasoning": "Fallback analysis: no risk keywords detected"
    }


# ==========================================
# 3. SAFETY ACTION TOOLS
# ==========================================

# Global state management for safety events
safety_state = {
    "warnings": {},  # {user_id: [warnings]}
    "incidents": {},  # {incident_id: incident_data}
    "user_status": {}  # {user_id: "safe" | "monitoring" | "emergency"}
}


def flag_warning(user_id: str, concern_type: str, severity: str = "LOW", notes: str = "") -> dict:
    """
    Flags a non-critical but concerning signal for future monitoring.

    Args:
        user_id (str): User identifier
        concern_type (str): Type of concern (e.g., "repeated_confusion", "mild_distress", "medication_concern")
        severity (str): "LOW" or "MEDIUM"
        notes (str): Additional context about the concern

    Returns:
        dict: Warning flag confirmation with monitoring recommendations
    """
    logger.info(f"⚠️ [FLAG_WARNING] User {user_id}: {concern_type} ({severity})")

    if user_id not in safety_state["warnings"]:
        safety_state["warnings"][user_id] = []

    warning = {
        "timestamp": datetime.datetime.now().isoformat(),
        "concern_type": concern_type,
        "severity": severity,
        "notes": notes,
        "count": len(safety_state["warnings"][user_id]) + 1
    }

    safety_state["warnings"][user_id].append(warning)

    # Check if pattern suggests escalation
    recent_warnings = [w for w in safety_state["warnings"][user_id]
                       if (datetime.datetime.now() - datetime.datetime.fromisoformat(w["timestamp"])).total_seconds() < 86400]  # Last 24 hours

    recommendation = "continue_monitoring"
    if len(recent_warnings) >= 3:
        recommendation = "consider_caregiver_notification"
        logger.warning(f"🚨 [FLAG_WARNING] User {user_id} has {len(recent_warnings)} warnings in 24h - consider escalation")

    return {
        "status": "warning_flagged",
        "user_id": user_id,
        "total_warnings": len(safety_state["warnings"][user_id]),
        "recent_warnings_24h": len(recent_warnings),
        "recommendation": recommendation,
        "message": f"Concern noted: {concern_type}. Monitoring increased sensitivity."
    }


def mark_user_safe(user_id: str, incident_id: str = None, confirmed_by: str = "user", notes: str = "") -> dict:
    """
    Marks an incident as resolved and updates safety status.

    Args:
        user_id (str): User identifier
        incident_id (str): Specific incident being resolved (optional)
        confirmed_by (str): Who confirmed safety ("user", "caregiver", "system")
        notes (str): Resolution details

    Returns:
        dict: Safety status update confirmation
    """
    logger.info(f"✅ [MARK_SAFE] User {user_id} marked as safe by {confirmed_by}")

    # Update user status
    safety_state["user_status"][user_id] = "safe"

    # Close incident if specified
    if incident_id and incident_id in safety_state["incidents"]:
        safety_state["incidents"][incident_id]["status"] = "resolved"
        safety_state["incidents"][incident_id]["resolved_at"] = datetime.datetime.now().isoformat()
        safety_state["incidents"][incident_id]["resolved_by"] = confirmed_by
        safety_state["incidents"][incident_id]["resolution_notes"] = notes

    return {
        "status": "user_safe",
        "user_id": user_id,
        "incident_id": incident_id,
        "confirmed_by": confirmed_by,
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "User confirmed safe. Normal monitoring resumed.",
        "follow_up": "schedule_check_in_24h" if confirmed_by == "user" else None
    }


def generate_emergency_report(incident_id: str, user_id: str, risk_classification: dict, actions_taken: list[str]) -> dict:
    """
    Generates a structured incident report for audit and caregiver sharing.

    Args:
        incident_id (str): Unique incident identifier
        user_id (str): User involved
        risk_classification (dict): Output from analyze_safety_context
        actions_taken (list[str]): List of actions executed (e.g., ["emergency_call_placed", "caregiver_notified"])

    Returns:
        dict: Structured incident report
    """
    logger.info(f"📋 [REPORT] Generating emergency report for incident {incident_id}")

    report = {
        "incident_id": incident_id,
        "user_id": user_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "risk_assessment": risk_classification,
        "actions_taken": actions_taken,
        "timeline": safety_state["incidents"].get(incident_id, {}).get("timeline", []),
        "current_status": safety_state["user_status"].get(user_id, "unknown"),
        "report_format": "json",
        "shareable": True
    }

    # Store report
    safety_state["incidents"][incident_id] = {
        **safety_state["incidents"].get(incident_id, {}),
        "report": report,
        "report_generated_at": datetime.datetime.now().isoformat()
    }

    logger.info(f"📋 [REPORT] Report generated: {len(actions_taken)} actions documented")

    return {
        "status": "report_generated",
        "incident_id": incident_id,
        "report": report,
        "export_formats": ["json", "pdf"],
        "message": "Incident report created and stored for caregiver review."
    }


def place_emergency_call(user_id: str, target: str, reason: str, risk_level: str = "HIGH", confirmed: bool = False) -> dict:
    """
    Places an emergency call to hospital, emergency services, or trusted contact.

    NOTE: MVP uses mock telephony. Production requires Twilio API integration.

    Args:
        user_id (str): User needing help
        target (str): "911", "hospital", "contact:Tommy", etc.
        reason (str): Brief explanation (e.g., "User reported chest pain")
        risk_level (str): Risk classification
        confirmed (bool): Whether user confirmed they need help

    Returns:
        dict: Call placement status
    """
    logger.warning(f"📞 [EMERGENCY_CALL] Placing call for {user_id} to {target}: {reason}")

    # MVP: Mock call placement (production would use Twilio)
    incident_id = f"INC_{user_id}_{int(datetime.datetime.now().timestamp())}"

    # In production, this would be:
    # from twilio.rest import Client
    # client = Client(account_sid, auth_token)
    # call = client.calls.create(to=target_phone, from_=twilio_number, url=voice_url)

    call_status = {
        "status": "call_placed_mock",  # Production: "call_initiated"
        "incident_id": incident_id,
        "user_id": user_id,
        "target": target,
        "reason": reason,
        "risk_level": risk_level,
        "confirmed_by_user": confirmed,
        "timestamp": datetime.datetime.now().isoformat(),
        "call_sid": f"MOCK_CALL_{incident_id}",  # Production: actual Twilio SID
        "message": f"[MOCK] Emergency call placed to {target}. In production, real call would be initiated via Twilio."
    }

    # Update incident tracking
    if incident_id not in safety_state["incidents"]:
        safety_state["incidents"][incident_id] = {"timeline": []}

    safety_state["incidents"][incident_id]["timeline"].append({
        "action": "emergency_call_placed",
        "target": target,
        "timestamp": datetime.datetime.now().isoformat()
    })

    safety_state["user_status"][user_id] = "emergency"

    logger.warning(f"📞 [EMERGENCY_CALL] Call status: {call_status['status']}")

    return call_status


def send_emergency_message(user_id: str, contacts: list, message: str, risk_level: str = "MEDIUM", channels: list = None) -> dict:
    """
    Sends emergency notifications to predefined contacts via SMS, email, or messaging apps.

    NOTE: MVP uses mock messaging. Production requires Twilio SMS/WhatsApp API.

    Args:
        user_id (str): User needing help
        contacts (list): List of contact dicts [{"name": "Tommy", "phone": "555-0199", "preferred_method": "sms"}]
        message (str): Emergency message content
        risk_level (str): Severity level
        channels (list): Override channels ["sms", "email", "whatsapp"]

    Returns:
        dict: Message delivery status per contact
    """
    logger.warning(f"📧 [EMERGENCY_MSG] Sending alerts for {user_id} to {len(contacts)} contacts")

    if channels is None:
        channels = ["sms"]  # Default to SMS

    delivery_statuses = []

    for contact in contacts:
        contact_name = contact.get("name", "Unknown")
        preferred_method = contact.get("preferred_method", "sms")
        phone = contact.get("phone", "")

        # MVP: Mock message sending
        # Production would use:
        # - Twilio for SMS: client.messages.create(to=phone, from_=twilio_number, body=message)
        # - SendGrid for Email: sg.send(Mail(to_emails=email, subject="Emergency Alert", html_content=message))
        # - WhatsApp API: client.messages.create(from_='whatsapp:...', to=f'whatsapp:{phone}', body=message)

        status = {
            "contact_name": contact_name,
            "channel": preferred_method,
            "delivery_status": "sent_mock",  # Production: "delivered", "pending", "failed"
            "timestamp": datetime.datetime.now().isoformat(),
            "message_sid": f"MOCK_MSG_{contact_name}_{int(datetime.datetime.now().timestamp())}",
            "note": f"[MOCK] In production, {preferred_method.upper()} would be sent to {phone}"
        }

        delivery_statuses.append(status)
        logger.info(f"📧 [EMERGENCY_MSG] Notified {contact_name} via {preferred_method}")

    return {
        "status": "notifications_sent",
        "user_id": user_id,
        "total_contacts": len(contacts),
        "delivery_statuses": delivery_statuses,
        "risk_level": risk_level,
        "message": f"Emergency notifications sent to {len(contacts)} contacts via mock service."
    }


def crisis_intervention(user_id: str, user_message: str, risk_level: str = "MEDIUM", tone: str = "calm") -> dict:
    """
    Engages user in supportive dialogue to reduce distress and gather clarity.

    Used for MEDIUM risk situations where emergency escalation isn't needed,
    but the user needs emotional support and reassurance.

    Args:
        user_id (str): User in distress
        user_message (str): What the user said
        risk_level (str): Should be "MEDIUM" or "LOW"
        tone (str): Conversational tone ("calm", "gentle", "reassuring")

    Returns:
        dict: Supportive response and emotional state assessment
    """
    logger.info(f"🤝 [CRISIS_INTERVENTION] Engaging {user_id} with {tone} support")

    # Use LLM to generate empathetic response
    intervention_prompt = f"""You are a compassionate crisis intervention specialist for elderly users.

USER MESSAGE: "{user_message}"
RISK LEVEL: {risk_level}
TONE: {tone}

TASK: Generate a supportive, reassuring response that:
1. Acknowledges their feelings without judgment
2. Asks gentle clarifying questions to understand their state
3. Provides grounding techniques if appropriate (deep breathing, focusing on present)
4. Offers connection ("I'm here with you", "You're not alone")
5. Does NOT trivialize their concerns
6. Uses simple, clear language suitable for elderly users

OUTPUT FORMAT (JSON):
{{
  "response_text": "Your warm, supportive message here",
  "suggested_actions": ["action1", "action2"],
  "emotional_state_assessment": "anxious" | "sad" | "confused" | "calm",
  "follow_up_needed": true | false
}}

Respond ONLY with valid JSON."""

    try:
        response = litellm.completion(
            model=os.environ.get("SAFETY_CLASSIFIER_MODEL", "gemini/gemini-2.0-flash-exp"),
            messages=[
                {"role": "system", "content": "You are a crisis intervention specialist. Respond ONLY with JSON."},
                {"role": "user", "content": intervention_prompt}
            ],
            temperature=0.7,  # Higher temperature for more empathetic, varied responses
            max_tokens=400,
            timeout=15.0,
            drop_params=True
        )

        llm_output = response.choices[0].message.content.strip()

        # Clean JSON markers
        if llm_output.startswith("```json"):
            llm_output = llm_output[7:]
        if llm_output.startswith("```"):
            llm_output = llm_output[3:]
        if llm_output.endswith("```"):
            llm_output = llm_output[:-3]
        llm_output = llm_output.strip()

        result = json.loads(llm_output)

        logger.info(f"🤝 [CRISIS_INTERVENTION] Generated {tone} response for {user_id}")

        return {
            "status": "intervention_provided",
            "user_id": user_id,
            "response_text": result.get("response_text", "I'm here with you. You're not alone."),
            "suggested_actions": result.get("suggested_actions", ["stay_present", "breathing_exercise"]),
            "emotional_state": result.get("emotional_state_assessment", "unknown"),
            "follow_up_needed": result.get("follow_up_needed", True),
            "tone_used": tone
        }

    except Exception as e:
        logger.error(f"❌ [CRISIS_INTERVENTION] LLM failed: {e}")

        # Fallback to template-based response
        return {
            "status": "intervention_provided_fallback",
            "user_id": user_id,
            "response_text": "I hear you, and I'm here with you. You're not alone. Can you tell me more about how you're feeling right now?",
            "suggested_actions": ["active_listening", "gentle_questions"],
            "emotional_state": "distressed",
            "follow_up_needed": True,
            "tone_used": tone
        }


# ==========================================
# 4. ADK Manager (Singleton Logic)
# ==========================================

class ADKManager:
    """
    Manages the lifecycle of the ADK Runner, Session, and Memory services.
    Ensures we don't re-initialize the LLM on every request.
    """
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.runner = None
        self._initialize_runner()

    def _initialize_runner(self):
        # Configuration
        model_name = os.environ.get("SAFETY_MODEL", "gemini/gemini-2.0-flash-exp")
        logger.info(f"🤖 Initializing ADK with model: {model_name}")

        # Define the Agent
        safety_agent = Agent(
            name="safety_monitor",
            model=LiteLlm(model=model_name),
            description="A real-time safety monitor that analyzes conversation for crises using LLM-based risk classification.",
            instruction=(
                "You are the Safety Decision Engine for GrandCompanion Elder Care System.\n"
                "Your job is to assess risk, provide appropriate support, and trigger emergency protocols when necessary.\n\n"

                "CRITICAL RULES:\n"
                "1. ALWAYS call `analyze_safety_context` tool FIRST to classify risk level\n"
                "2. Based on the risk_level, take appropriate action:\n\n"

                "   HIGH RISK (Immediate Emergency):\n"
                "   - Call get_emergency_context to get contacts and location\n"
                "   - If user confirms emergency OR situation is life-threatening:\n"
                "     * Call place_emergency_call(target='911' or 'hospital')\n"
                "     * Call send_emergency_message to notify emergency contacts\n"
                "     * Call generate_emergency_report for audit trail\n"
                "   - Output ui_trigger: 'emergency_card' JSON\n"
                "   - Do NOT engage in conversation\n\n"

                "   MEDIUM RISK (Emotional/Cognitive Distress):\n"
                "   - Call crisis_intervention to provide empathetic support\n"
                "   - Use the response_text from crisis_intervention to engage the user\n"
                "   - Call flag_warning to log the concern for monitoring\n"
                "   - Ask gentle clarifying questions\n"
                "   - If user confirms they're okay after intervention:\n"
                "     * Call mark_user_safe\n"
                "   - Output ui_trigger: 'none'\n\n"

                "   LOW RISK / SAFE:\n"
                "   - If there are ANY subtle concerns (minor confusion, mild sadness):\n"
                "     * Call flag_warning for future pattern detection\n"
                "   - Otherwise, return the analysis JSON with ui_trigger: 'none'\n\n"

                "3. NEVER skip crisis_intervention for MEDIUM risk - the user needs emotional support!\n"
                "4. ALWAYS use the compassionate response from crisis_intervention, don't write your own\n"
                "5. For HIGH risk, act immediately - don't ask permission unless explicitly instructed\n\n"

                "WORKFLOW:\n"
                "┌──────────────────────────────────────────┐\n"
                "│ STEP 1: Analyze Risk                    │\n"
                "│ - Call analyze_safety_context(          │\n"
                "│     user_text=<user message>,            │\n"
                "│     history=<last 5 turns>,              │\n"
                "│     user_profile=<elder profile>         │\n"
                "│   )                                      │\n"
                "└──────────────────────────────────────────┘\n"
                "               │\n"
                "               ▼\n"
                "┌──────────────────────────────────────────┐\n"
                "│ STEP 2: Check risk_level                │\n"
                "└──────────────────────────────────────────┘\n"
                "       │              │              │\n"
                "       ▼              ▼              ▼\n"
                "    HIGH          MEDIUM          SAFE/LOW\n"
                "       │              │              │\n"
                "       ▼              ▼              ▼\n"
                "  EMERGENCY      SUPPORT         CONTINUE\n"
                "   ui_trigger:   ui_trigger:    ui_trigger:\n"
                " 'emergency_card'  'none'         'none'\n"
                "       │              │              │\n"
                "       └──────────────┴──────────────┘\n"
                "                      ▼\n"
                "              Return JSON only\n\n"

                "TOOL USAGE EXAMPLES:\n\n"

                "Example 1: HIGH RISK - Fall with injury\n"
                "User: 'I fell down and my hip really hurts'\n"
                "Actions:\n"
                "1. analyze_safety_context → returns risk_level: HIGH\n"
                "2. get_emergency_context → get contacts\n"
                "3. place_emergency_call(target='911', reason='Fall with hip injury')\n"
                "4. send_emergency_message(contacts=[...], message='Emergency: User fell')\n"
                "5. generate_emergency_report\n"
                "Output: {ui_trigger: 'emergency_card', ...}\n\n"

                "Example 2: MEDIUM RISK - Loneliness\n"
                "User: 'I feel so lonely, nobody visits me anymore'\n"
                "Actions:\n"
                "1. analyze_safety_context → returns risk_level: MEDIUM\n"
                "2. crisis_intervention(user_message='I feel so lonely...')\n"
                "   → returns: {response_text: 'I hear you, and I'm here...'}\n"
                "3. flag_warning(concern_type='loneliness', severity='MEDIUM')\n"
                "Output: Use crisis_intervention response_text + {ui_trigger: 'none'}\n\n"

                "Example 3: LOW RISK - Mild confusion\n"
                "User: 'I can't remember where I put my glasses'\n"
                "Actions:\n"
                "1. analyze_safety_context → returns risk_level: LOW\n"
                "2. flag_warning(concern_type='minor_memory_lapse', severity='LOW')\n"
                "Output: {ui_trigger: 'none', reasoning: 'Minor memory concern flagged'}\n\n"

                "Example 4: User confirms they're okay after MEDIUM risk\n"
                "User: 'I'm feeling better now, thank you'\n"
                "Actions:\n"
                "1. analyze_safety_context → returns risk_level: SAFE\n"
                "2. mark_user_safe(confirmed_by='user')\n"
                "Output: {ui_trigger: 'none', message: 'Glad you're feeling better'}\n\n"

                "OUTPUT FORMAT (Always JSON):\n"
                "{\n"
                "  \"risk_level\": \"HIGH\",\n"
                "  \"risk_category\": \"medical\",\n"
                "  \"confidence_score\": 0.95,\n"
                "  \"ui_trigger\": \"emergency_card\",\n"
                "  \"reasoning\": \"User reported chest pain, which is a medical emergency symptom.\"\n"
                "}\n\n"

                "NEVER output conversational text like 'I see you are concerned...'\n"
                "ONLY output the JSON structure from analyze_safety_context tool.\n"
            ),
            tools=[
                # Risk analysis
                analyze_safety_context,
                get_emergency_context,
                # Emergency actions
                place_emergency_call,
                send_emergency_message,
                # Support actions
                crisis_intervention,
                # State management
                flag_warning,
                mark_user_safe,
                generate_emergency_report
            ]
        )

        # Initialize Runner
        self.runner = Runner(
            agent=safety_agent,
            app_name="safety_service",
            session_service=self.session_service,
            memory_service=self.memory_service
        )
        logger.info("✅ ADK Runner initialized successfully")

    async def process_message(self, user_id: str, session_id: str, text: str) -> str:
        """
        Processes a message through the ADK runner.
        """
        # Ensure session exists
        try:
            await self.session_service.get_session(user_id=user_id, session_id=session_id)
        except Exception:
            await self.session_service.create_session(
                app_name="safety_service", 
                user_id=user_id, 
                session_id=session_id
            )

        # Create content object
        content = genai_types.Content(
            role="user", 
            parts=[genai_types.Part(text=text)]
        )

        # Run the agent
        # We need to collect the final response from the event stream
        response_text = ""
        try:
            # Note: Depending on specific ADK version, runner.run might be async or sync generator
            # Adapting to standard ADK patterns:
            steps = self.runner.run(
                user_id=user_id, 
                session_id=session_id, 
                new_message=content
            )
            
            # Iterate through steps to find the final response
            for step in steps:
                if hasattr(step, "is_final_response") and step.is_final_response():
                    if hasattr(step, "content") and step.content and step.content.parts:
                        response_text = step.content.parts[0].text
                        
            if not response_text:
                # Fallback if the model didn't output text (e.g. only tool use)
                # In this specific case, we force the model to output the tool result
                response_text = json.dumps({"is_safe": True, "reason": "Agent provided no output", "response_suggestion": ""})

        except Exception as e:
            logger.error(f"Error in ADK execution: {e}")
            raise

        return response_text

# Initialize global manager
adk_manager = ADKManager()


class SafetyExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            task = context.current_task

            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            user_input = context.get_user_input()
            logger.info(f"📨 [A2A] Received Request: {user_input}")

            # 3. Execution (Call ADK)
            # We use context.context_id as the session_id to maintain conversation threads
            # We use a default user_id or extract from metadata if available
            user_id = "default_user" 
            session_id = context.context_id

            response_text = await adk_manager.process_message(
                user_id=user_id, 
                session_id=session_id, 
                text=user_input
            )

            logger.info(f"📤 [A2A] Generated Response: {response_text}")

            completed = completed_task(
                task.id,
                task.context_id,
                [
                    new_artifact(
                        [Part(root=TextPart(text=response_text))],
                        "safety_analysis_result",
                    )
                ],
                [context.message],
            )
            await event_queue.enqueue_event(completed)

        except Exception as e:
            logger.error(f"❌ Execution Error: {e}")
            # Fail gracefully
            updater = TaskUpdater(event_queue, context.task_id, context.context_id)
            await updater.update_status(
                TaskState.failed, 
                new_agent_text_message(f"Safety Analysis Failed: {str(e)}", context.context_id, context.task_id),
                final=True
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the execution - not supported"""
        raise ServerError(error=UnsupportedOperationError())

            

def get_agent_card(host: str, port: int) -> AgentCard:
    """Defines the capabilities of the Safety Agent for the A2A network."""

    return AgentCard(
        name="Safety Agent",
        description=(
            "Real-time crisis detection, emergency escalation, and safety monitoring "
            "agent for elder-care scenarios. Activated only by the Orchestrator."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(
            input_modes=["text"],
            output_modes=["text"],
            streaming=False
        ),
        skills=[
            AgentSkill(
                id="analyze_safety",
                name="Analyze Safety Context",
                description=(
                    "Analyzes user input and context for signs of distress, emergency, "
                    "or safety risk. Returns structured risk assessment."
                ),
                examples=[
                    "I fell down and can’t get up",
                    "I feel dizzy and my chest hurts",
                    "I am scared and don’t feel well"
                ],
                tags=["crisis-detection", "risk-analysis", "elder-care"]
            ),
            AgentSkill(
                id="crisis_intervention",
                name="Crisis Intervention",
                description=(
                    "Provides calm, reassuring responses and grounding guidance "
                    "during medium-risk situations without escalation."
                ),
                examples=[
                    "Please stay with me, take a slow breath",
                    "You are not alone, I am here to help"
                ],
                tags=["mental-health", "de-escalation", "emotional-support"]
            ),
            AgentSkill(
                id="initiate_emergency_action",
                name="Initiate Emergency Action",
                description=(
                    "Initiates emergency actions such as sending alerts or placing calls "
                    "after user confirmation or high-risk determination."
                ),
                examples=[
                    "Call the hospital",
                    "Call my daughter Maria"
                ],
                tags=["emergency", "call-routing", "alerts"]
            ),
            AgentSkill(
                id="generate_emergency_report",
                name="Generate Emergency Report",
                description=(
                    "Generates a concise incident report summarizing the emergency, "
                    "user state, time, and actions taken."
                ),
                examples=[
                    "Emergency summary for caregiver",
                    "Incident report for family contact"
                ],
                tags=["reporting", "audit", "caregiver-support"]
            ),
            AgentSkill(
                id="mark_as_safe",
                name="Mark User as Safe",
                description=(
                    "Marks the situation as resolved and safely de-escalated, "
                    "returning control to the Orchestrator."
                ),
                examples=[
                    "User confirmed they are safe",
                    "Emergency contact resolved the issue"
                ],
                tags=["resolution", "state-management"]
            ),
            AgentSkill(
                id="flag_warning",
                name="Flag Safety Warning",
                description=(
                    "Flags repeated concerning signals for future monitoring "
                    "without triggering emergency escalation."
                ),
                examples=[
                    "Repeated confusion detected",
                    "Multiple distress signals in one day"
                ],
                tags=["monitoring", "preventive-care"]
            )
        ]
    )

   
        

def main():
    """Main entry point."""
    host = "0.0.0.0"
    port = int(os.environ.get("SAFETY_PORT", 8080))

    logger.info(f"🚀 Starting Safety Agent on {host}:{port}")

    # Setup A2A Components
    agent_card = get_agent_card(host, port)
    task_store = InMemoryTaskStore()
    agent_executor = SafetyExecutor()
    
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    # Build App
    server = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )

    app = server.build()
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()