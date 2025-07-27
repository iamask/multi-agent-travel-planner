#!/bin/bash

# AI Research Assistant Activation Script
echo "🎓 AI Research Assistant - Multi-Agent System"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your OpenAI API key:"
    echo "OPENAI_API_KEY=your-api-key-here"
    exit 1
fi

echo "✅ Environment ready!"
echo ""
echo "🚀 Available commands:"
echo "  python ai_research_assistant.py     - Run the main AI Research Assistant"
echo "  python demo_research_assistant.py   - Run the demo script"
echo ""
echo "🎯 Example usage:"
echo "  python -c \"import asyncio; from ai_research_assistant import run_orchestrated_research; asyncio.run(run_orchestrated_research('What are the challenges in implementing AI in hospitals?'))\""
echo "" 