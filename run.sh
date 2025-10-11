#!/bin/bash

# Trading Agent Bot Startup Script

echo "🤖 Starting Trading Agent Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker detected. Starting with Docker Compose..."
    
    # Build and start the bot
    docker-compose up --build -d
    
    # Show logs
    echo "📋 Bot logs:"
    docker-compose logs -f trading-bot
else
    echo "🐍 Docker not found. Starting with Python..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found!"
        exit 1
    fi
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    
    # Start the bot
    echo "🚀 Starting bot..."
    python3 bot.py
fi