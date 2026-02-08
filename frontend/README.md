# AI-Controlled Onboarding UI

An intelligent onboarding system where an AI agent dynamically controls the user interface flow, validates input, personalizes content, and creates adaptive experiences.

## 🎯 Overview

This prototype demonstrates **AG-UI (Agent-Generated UI)** - a pattern where AI agents don't just respond to users but actively control and manipulate the user interface based on context, user behavior, and intelligent decision-making.

### Key Features

- **AI-Driven Flow Control**: Agent decides which steps to show and when
- **Real-time Validation**: LLM-powered input validation with helpful suggestions
- **Dynamic Form Generation**: Forms adapt based on previous answers
- **Personalized Content**: Each step is tailored to the user's journey
- **Progress Tracking**: Visual feedback on onboarding completion
- **Error Handling**: Intelligent error messages and recovery

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   React UI      │ ◄─────► │  Agent Server   │
│  (Frontend)     │  HTTP   │   (Python)      │
└─────────────────┘         └─────────────────┘
        │                            │
        │                            │
        ▼                            ▼
  ┌──────────┐              ┌──────────────┐
  │ UI State │              │ Ollama LLM   │
  └──────────┘              └──────────────┘
```

### Communication Flow

1. **User Action** → React UI sends action to agent
2. **Agent Processing** → Agent uses LLM to make decisions
3. **UI Commands** → Agent responds with UI manipulation commands
4. **UI Update** → React processes commands and updates interface

### UI Command Types

```typescript
{
  action: 'navigate' | 'update' | 'validate' | 'show_error',
  component: string,
  props: Record<string, any>
}
```

## 📦 Installation

### Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Ollama (for local LLM)

### Backend Setup

1. Install Python dependencies:
```bash
pip install anthropic-a2a uvicorn requests
```

2. Install and start Ollama:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1:8b
```

3. Start the agent server:
```bash
python onboarding_agent_server.py
```

The agent will start on `http://localhost:8083`

### Frontend Setup

1. Install dependencies:
```bash
cd react-onboarding-ui
npm install
```

2. Start the React app:
```bash
npm start
```

The UI will open at `http://localhost:3000`

## 🚀 Usage

### Basic Flow

1. **Initialize**: UI calls agent with `init` action
2. **Step Progression**: User fills out form → Agent validates → Moves to next step
3. **Completion**: All steps complete → Agent shows completion screen

### Agent Communication

```typescript
// Initialize onboarding
const response = await sendAction('init');

// Submit step data
const response = await sendAction('submit_step', {
  full_name: 'John Doe',
  email: 'john@example.com'
});

// Validate field in real-time
const response = await sendAction('validate', {
  field: 'email',
  value: 'john@example.com'
});

// Navigate back
const response = await sendAction('navigate', {
  direction: 'back'
});
```

### Agent Response Format

```json
{
  "text": "Great! Let's move on to preferences.",
  "ui_commands": [
    {
      "action": "navigate",
      "component": "onboarding_flow",
      "props": {
        "step": "preferences",
        "data": {
          "title": "Customize your experience",
          "fields": [...]
        }
      }
    }
  ],
  "onboarding_state": {
    "current_step": 2,
    "step_name": "preferences",
    "progress": 40,
    "is_complete": false
  }
}
```

## 🎨 Customization

### Adding New Steps

1. **Update agent flow** in `onboarding_agent_server.py`:
```python
self.onboarding_flow = [
    "welcome",
    "basic_info",
    "preferences",
    "new_step",  # Add here
    "goals",
    "confirmation"
]
```

2. **Create step component** in `src/components/steps/`:
```tsx
export const NewStep: React.FC<StepProps> = ({ data, onSubmit }) => {
  // Your step implementation
};
```

3. **Register in OnboardingFlow.tsx**:
```tsx
case 'new_step':
  return <NewStep {...commonProps} />;
```

### Customizing Agent Logic

The agent uses LLM to make intelligent decisions. You can customize prompts in:

- `validate_with_llm()`: Validation logic
- `generate_next_step_config()`: Step personalization
- `generate_transition_message()`: User-facing messages

### Styling

All styles are in component-specific CSS files:
- `OnboardingFlow.css`: Main layout and animations
- `DynamicForm.css`: Form styling
- `ProgressBar.css`: Progress indicator

## 🔧 Advanced Features

### Dynamic Form Generation

The agent can generate custom form fields based on context:

```python
def generate_next_step_config(self, step: str, previous_data: Dict):
    # Agent uses LLM to create personalized fields
    prompt = f"Create fields for {step} based on {previous_data}"
    return self._call_ollama(prompt)
```

### Real-time Validation

Fields are validated as user types:

```tsx
<input
  onChange={(e) => {
    handleFieldChange(field.name, e.target.value);
    onValidate?.(field.name, e.target.value);
  }}
/>
```

### State Persistence

The agent maintains state across interactions:

```python
class OnboardingState:
    def __init__(self):
        self.current_step = 0
        self.user_data = {}
        self.completed_steps = []
```

## 📊 Example Use Cases

### 1. Adaptive Questioning

Agent adjusts questions based on previous answers:
- User is "Beginner" → Shows detailed explanations
- User is "Expert" → Skips basic questions

### 2. Smart Validation

Instead of rigid rules, LLM validates with context:
- "john@" → "Email seems incomplete, did you mean john@example.com?"
- Age: 150 → "That doesn't seem right. Please check your age."

### 3. Personalized Messaging

Agent generates encouraging messages:
- Fast progression → "You're doing great!"
- Struggling → "No rush, take your time."

## 🔒 Environment Variables

```bash
# Agent Server
OLLAMA_MODEL=llama3.1:8b          # LLM model to use
OLLAMA_BASE_URL=http://localhost:11434  # Ollama API URL

# React App
REACT_APP_AGENT_URL=http://localhost:8083  # Agent server URL
```

## 🧪 Testing

```bash
# Test agent server
curl -X POST http://localhost:8083/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "{\"action\": \"init\"}"}]
    }
  }'
```

## 📝 API Reference

### Agent Endpoints

**POST /process**
- Processes user actions and returns UI commands
- Request: A2A message format
- Response: Agent response with UI commands

### Hook Functions

**useOnboardingAgent(agentUrl)**
- `sendAction(action, data)`: Communicate with agent
- `isLoading`: Loading state
- `error`: Error state

## 🎭 Demo Scenarios

### Scenario 1: Happy Path
1. User arrives → Welcome screen
2. Fills basic info → Agent validates
3. Selects preferences → Agent personalizes next step
4. Sets goals → Completion screen

### Scenario 2: Validation Errors
1. User enters invalid email
2. Agent shows inline error with suggestion
3. User corrects → Agent confirms and proceeds

### Scenario 3: Navigation
1. User completes step 2
2. Realizes mistake on step 1
3. Clicks back → Returns to step 1
4. Corrects data → Proceeds forward

## 🚧 Limitations

- Requires Ollama running locally (can be swapped with any LLM API)
- Agent state is in-memory (use Redis/DB for production)
- No authentication (add as needed)
- Single user session (add session management for multi-user)

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] A/B testing different flows
- [ ] Analytics and heatmaps
- [ ] Voice input integration
- [ ] Accessibility improvements
- [ ] Mobile app version
- [ ] Agent learning from user behavior

## 📚 Resources

- [A2A Protocol Documentation](https://github.com/anthropics/anthropic-agent-to-agent)
- [Ollama Documentation](https://ollama.ai)
- [React Documentation](https://react.dev)

## 🤝 Contributing

Contributions are welcome! This is a prototype demonstrating AG-UI concepts.

## 📄 License

MIT License - feel free to use in your projects!

---

Built with ❤️ using AI Agents, React, and Ollama
