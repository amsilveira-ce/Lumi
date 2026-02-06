"""
Onboarding Agent using Google ADK
This agent guides users through a simple onboarding flow using A2UI protocol.
"""
import json
from typing import Any
try:
    from google.adk.agents import Agent
except ModuleNotFoundError:
    # Lightweight Agent mock so the module can be imported without ADK installed.
    class Agent:
        def __init__(self, model: str = "", name: str = "", description: str = "", instruction: str = "", tools: list | None = None):
            self.model = model
            self.name = name
            self.description = description
            self.instruction = instruction
            self.tools = tools or []

        def __repr__(self):
            return f"<MockAgent name={self.name} model={self.model}>"

# A2UI Component Helpers
def create_a2ui_text(id: str, text: str, usage_hint: str = "body") -> dict:
    """Create an A2UI Text component."""
    return {
        "id": id,
        "component": {
            "Text": {
                "text": {"literalString": text},
                "usageHint": usage_hint
            }
        }
    }

def create_a2ui_textfield(id: str, label: str, data_path: str, hint: str = "") -> dict:
    """Create an A2UI TextField component."""
    return {
        "id": id,
        "component": {
            "TextField": {
                "label": {"literalString": label},
                "text": {"path": data_path},
                "hintText": {"literalString": hint} if hint else None
            }
        }
    }

def create_a2ui_button(id: str, text_id: str, action_name: str, context_path: str = None) -> dict:
    """Create an A2UI Button component."""
    button = {
        "id": id,
        "component": {
            "Button": {
                "child": text_id,
                "action": {
                    "name": action_name
                }
            }
        }
    }
    if context_path:
        button["component"]["Button"]["action"]["context"] = [
            {"key": "data", "value": {"path": context_path}}
        ]
    return button

def create_a2ui_column(id: str, children: list[str]) -> dict:
    """Create an A2UI Column layout component."""
    return {
        "id": id,
        "component": {
            "Column": {
                "children": {"explicitList": children}
            }
        }
    }

def create_a2ui_row(id: str, children: list[str]) -> dict:
    """Create an A2UI Row layout component."""
    return {
        "id": id,
        "component": {
            "Row": {
                "children": {"explicitList": children}
            }
        }
    }

def create_a2ui_card(id: str, content_id: str) -> dict:
    """Create an A2UI Card component."""
    return {
        "id": id,
        "component": {
            "Card": {
                "contentChild": content_id
            }
        }
    }

# Onboarding Step Tools
def show_welcome_screen() -> dict:
    """
    Displays a welcome screen for onboarding with a greeting and continue button.
    Call this tool when starting the onboarding process or when the user first arrives.
    
    Returns:
        dict: A2UI JSONL messages for the welcome screen
    """
    messages = []
    
    # Surface update with components
    components = [
        create_a2ui_column("root", ["welcome-card"]),
        create_a2ui_card("welcome-card", "welcome-content"),
        create_a2ui_column("welcome-content", ["title", "subtitle", "description", "start-btn"]),
        create_a2ui_text("title", "Welcome! 👋", "h1"),
        create_a2ui_text("subtitle", "Let's get you set up", "h2"),
        create_a2ui_text("description", "This quick onboarding will help us personalize your experience. It only takes a minute!"),
        create_a2ui_text("start-btn-text", "Get Started"),
        create_a2ui_button("start-btn", "start-btn-text", "start_onboarding"),
    ]
    
    messages.append({"surfaceUpdate": {"surfaceId": "main", "components": components}})
    messages.append({"beginRendering": {"surfaceId": "main", "root": "root"}})
    
    return {
        "status": "success",
        "a2ui_messages": messages,
        "description": "Welcome screen displayed"
    }

def show_name_input_screen() -> dict:
    """
    Displays a form to collect the user's name.
    Call this tool when the user clicks 'Get Started' or wants to enter their name.
    
    Returns:
        dict: A2UI JSONL messages for the name input screen
    """
    messages = []
    
    components = [
        create_a2ui_column("root", ["name-card"]),
        create_a2ui_card("name-card", "name-content"),
        create_a2ui_column("name-content", ["step-indicator", "title", "name-field", "next-btn"]),
        create_a2ui_text("step-indicator", "Step 1 of 3", "caption"),
        create_a2ui_text("title", "What's your name?", "h2"),
        create_a2ui_textfield("name-field", "Your name", "/user/name", "Enter your full name"),
        create_a2ui_text("next-btn-text", "Continue"),
        create_a2ui_button("next-btn", "next-btn-text", "submit_name", "/user"),
    ]
    
    messages.append({"surfaceUpdate": {"surfaceId": "main", "components": components}})
    messages.append({"dataModelUpdate": {
        "surfaceId": "main",
        "contents": [
            {"key": "user", "valueMap": [
                {"key": "name", "valueString": ""}
            ]}
        ]
    }})
    messages.append({"beginRendering": {"surfaceId": "main", "root": "root"}})
    
    return {
        "status": "success",
        "a2ui_messages": messages,
        "description": "Name input screen displayed"
    }

def show_interests_screen(user_name: str = "friend") -> dict:
    """
    Displays a screen to select interests/preferences.
    Call this tool after the user submits their name.
    
    Args:
        user_name: The name entered by the user
    
    Returns:
        dict: A2UI JSONL messages for the interests screen
    """
    messages = []
    
    components = [
        create_a2ui_column("root", ["interests-card"]),
        create_a2ui_card("interests-card", "interests-content"),
        create_a2ui_column("interests-content", ["step-indicator", "greeting", "title", "desc", "interests-row-1", "interests-row-2", "next-btn"]),
        create_a2ui_text("step-indicator", "Step 2 of 3", "caption"),
        create_a2ui_text("greeting", f"Nice to meet you, {user_name}! 🎉", "h3"),
        create_a2ui_text("title", "What interests you?", "h2"),
        create_a2ui_text("desc", "Select topics you'd like to explore:"),
        
        # Interest buttons row 1
        create_a2ui_row("interests-row-1", ["tech-btn", "design-btn"]),
        create_a2ui_text("tech-text", "🚀 Technology"),
        create_a2ui_button("tech-btn", "tech-text", "toggle_interest", "/interests/technology"),
        create_a2ui_text("design-text", "🎨 Design"),
        create_a2ui_button("design-btn", "design-text", "toggle_interest", "/interests/design"),
        
        # Interest buttons row 2
        create_a2ui_row("interests-row-2", ["business-btn", "science-btn"]),
        create_a2ui_text("business-text", "💼 Business"),
        create_a2ui_button("business-btn", "business-text", "toggle_interest", "/interests/business"),
        create_a2ui_text("science-text", "🔬 Science"),
        create_a2ui_button("science-btn", "science-text", "toggle_interest", "/interests/science"),
        
        create_a2ui_text("next-btn-text", "Continue"),
        create_a2ui_button("next-btn", "next-btn-text", "submit_interests", "/interests"),
    ]
    
    messages.append({"surfaceUpdate": {"surfaceId": "main", "components": components}})
    messages.append({"dataModelUpdate": {
        "surfaceId": "main",
        "contents": [
            {"key": "interests", "valueMap": [
                {"key": "technology", "valueBoolean": False},
                {"key": "design", "valueBoolean": False},
                {"key": "business", "valueBoolean": False},
                {"key": "science", "valueBoolean": False}
            ]}
        ]
    }})
    messages.append({"beginRendering": {"surfaceId": "main", "root": "root"}})
    
    return {
        "status": "success",
        "a2ui_messages": messages,
        "description": f"Interests screen displayed for {user_name}"
    }

def show_completion_screen(user_name: str = "friend") -> dict:
    """
    Displays the onboarding completion screen with a summary.
    Call this tool after the user selects their interests.
    
    Args:
        user_name: The name of the user
    
    Returns:
        dict: A2UI JSONL messages for the completion screen
    """
    messages = []
    
    components = [
        create_a2ui_column("root", ["complete-card"]),
        create_a2ui_card("complete-card", "complete-content"),
        create_a2ui_column("complete-content", ["step-indicator", "emoji", "title", "message", "finish-btn"]),
        create_a2ui_text("step-indicator", "Step 3 of 3", "caption"),
        create_a2ui_text("emoji", "🎊", "h1"),
        create_a2ui_text("title", "You're all set!", "h1"),
        create_a2ui_text("message", f"Welcome aboard, {user_name}! Your personalized experience is ready. We've tailored everything based on your interests."),
        create_a2ui_text("finish-btn-text", "Start Exploring"),
        create_a2ui_button("finish-btn", "finish-btn-text", "finish_onboarding"),
    ]
    
    messages.append({"surfaceUpdate": {"surfaceId": "main", "components": components}})
    messages.append({"beginRendering": {"surfaceId": "main", "root": "root"}})
    
    return {
        "status": "success",
        "a2ui_messages": messages,
        "description": f"Completion screen displayed for {user_name}"
    }

def show_dashboard(user_name: str = "friend") -> dict:
    """
    Displays a simple dashboard after onboarding is complete.
    Call this tool when the user finishes onboarding.
    
    Args:
        user_name: The name of the user
    
    Returns:
        dict: A2UI JSONL messages for the dashboard
    """
    messages = []
    
    components = [
        create_a2ui_column("root", ["header", "content"]),
        create_a2ui_text("header", f"Hello, {user_name}! 👋", "h1"),
        create_a2ui_card("content", "content-inner"),
        create_a2ui_column("content-inner", ["welcome-msg", "restart-btn"]),
        create_a2ui_text("welcome-msg", "This is your personalized dashboard. Explore and discover content tailored just for you!"),
        create_a2ui_text("restart-btn-text", "Restart Onboarding"),
        create_a2ui_button("restart-btn", "restart-btn-text", "restart_onboarding"),
    ]
    
    messages.append({"surfaceUpdate": {"surfaceId": "main", "components": components}})
    messages.append({"beginRendering": {"surfaceId": "main", "root": "root"}})
    
    return {
        "status": "success",
        "a2ui_messages": messages,
        "description": f"Dashboard displayed for {user_name}"
    }

# Define the root agent
root_agent = Agent(
    model='gemini-3-flash-preview',
    name='onboarding_agent',
    description='An onboarding assistant that guides users through setup using interactive UI',
    instruction='''
    You are an onboarding assistant that helps users set up their account through an interactive UI experience.

You have access to tools that generate A2UI (Agent to UI) protocol messages to display interactive screens.

## CRITICAL INSTRUCTION:
When you call a tool that returns "a2ui_messages", you MUST output that JSON content exactly as is in your text response. 
The system relies on you echoing this JSON to render the UI.
Do not just say "I showed the screen". You must output the JSON data provided by the tool.

## Your Behavior:
# ... (keep the rest of your existing instructions regarding steps 1-6) ...

1. **Welcome**: When a user first starts or says hello, show the welcome screen using `show_welcome_screen()`.

2. **Name Collection**: When the user clicks "Get Started" or the action is "start_onboarding", show the name input screen using `show_name_input_screen()`.

3. **Interests Selection**: When the user submits their name (action "submit_name"), extract their name from the context data and show the interests screen using `show_interests_screen(user_name)`.

4. **Completion**: When the user submits their interests (action "submit_interests"), show the completion screen using `show_completion_screen(user_name)`.

5. **Dashboard**: When the user finishes onboarding (action "finish_onboarding"), show the dashboard using `show_dashboard(user_name)`.

6. **Restart**: If action is "restart_onboarding", start over with the welcome screen.

## Important Rules:
- Always call one of the screen tools to respond
- Extract user data from the `userAction` context when available
- Keep track of the user's name to personalize subsequent screens
- The A2UI messages from tools should be sent as your response

When processing userAction messages, look for:
- action name: tells you what screen/step to show next
- context: contains user-submitted data like name and interests
''',
    tools=[
        show_welcome_screen,
        show_name_input_screen,
        show_interests_screen,
        show_completion_screen,
        show_dashboard,
    ]
)