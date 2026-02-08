#!/bin/bash

# GrandCompanion - Start All Backend Agents
# This script starts all 4 backend agents in the background

echo "🚀 Starting GrandCompanion Backend Agents..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434 > /dev/null; then
    echo "❌ Ollama is not running!"
    echo "   Start it with: ollama serve"
    echo "   Or ensure llama3.1:8b is installed: ollama pull llama3.1:8b"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Kill any existing agents
echo "🧹 Cleaning up existing agents..."
pkill -f "safety/server.py" 2>/dev/null
pkill -f "conversation_agent/server.py" 2>/dev/null
pkill -f "memory_agent/server.py" 2>/dev/null
pkill -f "orchestrator/server.py" 2>/dev/null
sleep 2

# Start agents in order
echo "Starting agents..."
echo ""

# 1. Safety Agent (8080)
echo "📡 Starting Safety Agent (port 8080)..."
cd src/safety
nohup python server.py > safety.log 2>&1 &
SAFETY_PID=$!
cd ../..
sleep 2

# 2. Conversation Agent (8081)
echo "💬 Starting Conversation Agent (port 8081)..."
cd src/conversation_agent
nohup python server.py > conversation.log 2>&1 &
CONV_PID=$!
cd ../..
sleep 2

# 3. Memory Agent (8083)
echo "🧠 Starting Memory Agent (port 8083)..."
cd src/memory_agent
nohup python server.py > memory.log 2>&1 &
MEMORY_PID=$!
cd ../..
sleep 2

# 4. Orchestrator (8082)
echo "🎯 Starting Orchestrator (port 8082)..."
cd src/orchestrator
nohup python server.py > orchestrator.log 2>&1 &
ORCH_PID=$!
cd ../..
sleep 3

# Verify all agents are running
echo ""
echo "🔍 Verifying agents..."
echo ""

check_agent() {
    local name=$1
    local port=$2

    if curl -s -m 2 http://localhost:$port > /dev/null 2>&1; then
        echo "✅ $name (port $port) - RUNNING"
        return 0
    else
        echo "❌ $name (port $port) - FAILED"
        return 1
    fi
}

check_agent "Safety Agent" 8080
check_agent "Conversation Agent" 8081
check_agent "Orchestrator" 8082
check_agent "Memory Agent" 8083

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Backend agents are running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Process IDs:"
echo "   Safety Agent:       $SAFETY_PID"
echo "   Conversation Agent: $CONV_PID"
echo "   Memory Agent:       $MEMORY_PID"
echo "   Orchestrator:       $ORCH_PID"
echo ""
echo "📝 Log files:"
echo "   src/safety/safety.log"
echo "   src/conversation_agent/conversation.log"
echo "   src/memory_agent/memory.log"
echo "   src/orchestrator/orchestrator.log"
echo ""
echo "🛑 To stop all agents:"
echo "   ./stop_all.sh"
echo "   or: pkill -f 'python.*server.py'"
echo ""
echo "▶️  Next step: Start the frontend"
echo "   cd ../frontend && npm start"
echo ""
