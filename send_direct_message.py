#!/usr/bin/env python3
"""
Send Direct Message
This script sends a direct message to Telegram using a different session file.
"""

import os
import asyncio
import time
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
DIRECT_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'direct_message_session')

# Use the web login session instead
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')

async def send_direct_message():
    """Send a direct message to Telegram."""
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        await client.connect()
        
        # Check if authorized
        if not await client.is_user_authorized():
            print("Not authorized. Please log in first.")
            return
        
        # Send a direct message to ourselves
        print("Sending a direct message to ourselves...")
        timestamp = time.strftime("%H:%M:%S")
        await client.send_message('me', f'Test direct message from send_direct_message.py at {timestamp}')
        print("Direct message sent. Check if you receive an SMS.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        await client.disconnect()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(send_direct_message()) 