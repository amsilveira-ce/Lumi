#!/bin/bash

# GrandCompanion - Stop All Backend Agents

echo "🛑 Stopping GrandCompanion Backend Agents..."
echo ""

# Kill all Python server processes
pkill -f "safety/server.py"
pkill -f "conversation_agent/server.py"
pkill -f "memory_agent/server.py"
pkill -f "orchestrator/server.py"

sleep 2

# Verify all stopped
echo "🔍 Verifying agents stopped..."
echo ""

if pgrep -f "safety/server.py" > /dev/null; then
    echo "⚠️  Safety Agent still running"
else
    echo "✅ Safety Agent stopped"
fi

if pgrep -f "conversation_agent/server.py" > /dev/null; then
    echo "⚠️  Conversation Agent still running"
else
    echo "✅ Conversation Agent stopped"
fi

if pgrep -f "memory_agent/server.py" > /dev/null; then
    echo "⚠️  Memory Agent still running"
else
    echo "✅ Memory Agent stopped"
fi

if pgrep -f "orchestrator/server.py" > /dev/null; then
    echo "⚠️  Orchestrator still running"
else
    echo "✅ Orchestrator stopped"
fi

echo ""
echo "✨ All backend agents stopped"
echo ""
