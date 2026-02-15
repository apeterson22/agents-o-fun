#!/bin/bash
# Startup script for agents-o-fun with OpenClaw orchestration
#
# This script starts all components of the AI agent system:
# 1. Trading Agent API (port 8081)
# 2. Trading Dashboard (port 8050)
# 3. OpenClaw Gateway (port 18789)

set -e

echo "🦞 Starting agents-o-fun with OpenClaw..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    echo "Please install Node.js >= 22 from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is required but not installed."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.openclaw ]; then
        echo "⚠️  No .env file found. Using .env.openclaw as template."
        echo "   Please copy .env.openclaw to .env and configure your API keys."
        cp .env.openclaw .env
    else
        echo "Error: No .env file found."
        echo "Please create a .env file with your API keys."
        exit 1
    fi
fi

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
if ! pip3 install -q -r requirements.txt; then
    echo "⚠️  Warning: Some Python dependencies failed to install."
    echo "   You may need to install them manually: pip3 install -r requirements.txt"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down agents..."
    if [ ! -z "$TRADING_PID" ]; then
        kill $TRADING_PID 2>/dev/null || true
    fi
    if [ ! -z "$OPENCLAW_PID" ]; then
        kill $OPENCLAW_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Trading Agent in background
echo "📈 Starting Trading Agent (API: http://localhost:8081, Dashboard: http://localhost:8050)..."
python3 main.py > logs/trading-agent.log 2>&1 &
TRADING_PID=$!

# Wait a bit for the trading agent to start
sleep 3

# Start OpenClaw Gateway in background
echo "🦞 Starting OpenClaw Gateway (http://localhost:18789)..."
npx openclaw gateway --port 18789 --verbose > logs/openclaw-gateway.log 2>&1 &
OPENCLAW_PID=$!

echo ""
echo "✅ All agents started!"
echo ""
echo "Services running:"
echo "  - Trading Agent API:  http://localhost:8081"
echo "  - Trading Dashboard:  http://localhost:8050"
echo "  - OpenClaw Gateway:   http://localhost:18789"
echo ""
echo "Logs:"
echo "  - Trading Agent: logs/trading-agent.log"
echo "  - OpenClaw:      logs/openclaw-gateway.log"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for processes
wait
