#!/usr/bin/env python3
"""
Send Test Message
This script sends a test message to ourselves on Telegram.
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

# Create a directory for Telegram sessions
TELEGRAM_SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_sessions')
os.makedirs(TELEGRAM_SESSIONS_DIR, exist_ok=True)
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')

async def send_test_message():
    """Send a test message to ourselves."""
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    # Connect to Telegram
    await client.connect()
    
    # Check if authorized
    if not await client.is_user_authorized():
        print("Not authorized. Please log in first.")
        return
    
    # Send a test message to ourselves
    print("Sending a test message to ourselves...")
    await client.send_message('me', f'Test message from send_test_message.py at {asyncio.get_event_loop().time()}')
    print("Test message sent. Check if you receive an SMS.")
    
    # Disconnect
    await client.disconnect()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(send_test_message()) 