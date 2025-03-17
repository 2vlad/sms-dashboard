#!/bin/bash
cd "$(dirname "$0")"

# Check if the app is already running
PORT=5001
if lsof -i :$PORT > /dev/null; then
    echo "Application is already running on port $PORT"
    echo "Stopping the existing process..."
    PID=$(lsof -i :$PORT -t)
    kill $PID
    sleep 2
    
    # Check if the process was killed
    if lsof -i :$PORT > /dev/null; then
        echo "Failed to stop the existing process. Please stop it manually."
        exit 1
    else
        echo "Existing process stopped successfully."
    fi
fi

# Make sure the session directories exist
mkdir -p flask_sessions
mkdir -p telegram_sessions

# Run the application
echo "Starting the application on port $PORT..."
python3 web_app.py > app.log 2>&1 