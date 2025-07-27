#!/bin/bash

# Multi-Agent Travel Planner Activation Script
echo "✈️ Multi-Agent Travel Planner System"
echo "====================================="

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
echo "  python travel_planner.py     - Run the Multi-Agent Travel Planner"
echo ""
echo "🎯 Example usage:"
echo "  python -c \"import asyncio; from travel_planner import run_simple_travel_planner; asyncio.run(run_simple_travel_planner('Plan a trip to Japan for cherry blossoms'))\""
echo "" 