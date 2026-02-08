# Quick Start Guide

Get the AI-controlled onboarding system running in 5 minutes!

## ⚡ Quick Setup

### 1. Install Ollama (One-time setup)

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai

# Pull the model
ollama pull llama3.1:8b
```

### 2. Start the Agent Server

```bash
# From the root directory
python onboarding_agent_server.py
```

You should see:
```
🚀 Starting AI-Driven Onboarding Agent on port 8083...
```

### 3. Start the React App

```bash
# In a new terminal
cd react-onboarding-ui
npm install
npm start
```

Browser opens at `http://localhost:3000` 🎉

## 🎮 Testing the Flow

### Test 1: Complete Onboarding

1. Click "Get Started" on welcome screen
2. Fill in your name and email
3. Select 2-3 interests
4. Write a goal
5. See completion screen!

### Test 2: Validation

1. Enter just "john" in email field
2. Watch the agent suggest "john@example.com"
3. Try entering age as "200"
4. See intelligent validation message

### Test 3: Navigation

1. Complete step 1
2. Click "Back" button
3. Notice state is preserved
4. Continue forward

## 🔍 Behind the Scenes

Watch the terminal where the agent runs to see:

```
📥 Received: {"action": "init"}
🤖 Response: Welcome! Let's begin your onboarding journey.
🎨 UI Commands: 1

📥 Received: {"action": "submit_step", "data": {...}}
🤖 Response: Great! Let's move on to preferences.
🎨 UI Commands: 1
```

## 🛠️ Customizing

### Change Welcome Message

Edit [onboarding_agent_server.py](onboarding_agent_server.py#L120):

```python
def handle_init(self):
    commands = [
        UICommand(
            action="navigate",
            component="onboarding_flow",
            props={
                "step": "welcome",
                "data": {
                    "title": "Your Custom Welcome!",  # Change this
                    "subtitle": "Your custom subtitle",  # And this
                    "features": [  # Add features
                        "Fast setup",
                        "AI-powered",
                        "Beautiful UI"
                    ]
                }
            }
        )
    ]
    return "Your custom message", commands
```

### Add a New Field

Edit the `generate_next_step_config()` method:

```python
"basic_info": {
    "title": "Tell us about yourself",
    "fields": [
        # ... existing fields ...
        {
            "name": "company",
            "label": "Company",
            "type": "text",
            "required": False
        }
    ]
}
```

### Change Colors

Edit [OnboardingFlow.css](src/components/OnboardingFlow.css#L3):

```css
.onboarding-flow {
  background: linear-gradient(135deg, #your-color 0%, #another-color 100%);
}
```

## 🐛 Troubleshooting

### Agent not responding?

```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Should return: {"version":"..."}
```

### CORS errors?

The agent server includes CORS headers. If issues persist:

```python
# Add to onboarding_agent_server.py
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Port already in use?

```bash
# Change agent port
PORT=8084 python onboarding_agent_server.py

# Update React hook
# In useOnboardingAgent.ts, change default URL
const agentUrl = 'http://localhost:8084'
```

## 🎯 Next Steps

1. **Read the [README.md](README.md)** for full documentation
2. **Explore the code** - start with `OnboardingFlow.tsx`
3. **Customize the flow** - add your own steps
4. **Deploy** - see deployment guide below

## 🚀 Deployment

### Backend (Agent)

```bash
# Using Docker
docker build -t onboarding-agent .
docker run -p 8083:8083 onboarding-agent

# Using systemd
sudo systemctl enable onboarding-agent
sudo systemctl start onboarding-agent
```

### Frontend (React)

```bash
# Build for production
npm run build

# Deploy to Vercel/Netlify/etc
# Update REACT_APP_AGENT_URL to production URL
```

## 💡 Tips

- **Use the browser DevTools** to see agent responses
- **Watch the agent terminal** for detailed logs
- **Try different LLM models** by changing `OLLAMA_MODEL`
- **Experiment with prompts** in the agent code

## 📞 Need Help?

- Check the [README.md](README.md) for detailed docs
- Review the code comments
- Test the agent directly with curl (see README)

---

Happy building! 🎉
