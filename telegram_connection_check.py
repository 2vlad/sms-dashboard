#!/usr/bin/env python3
"""
Telegram Connection Check
This script checks the Telegram connection status and displays diagnostic information.
"""

import os
import asyncio
import logging
import sqlite3
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

# Paths
TELEGRAM_SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_sessions')
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')
DATABASE_PATH = 'forwarder.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def check_telegram_connection():
    """Check the Telegram connection status and display diagnostic information."""
    logger.info("Checking Telegram connection status...")
    
    # Check if the session file exists
    session_file = f"{WEB_LOGIN_SESSION_PATH}.session"
    if os.path.exists(session_file):
        logger.info(f"Session file exists: {session_file}")
        file_size = os.path.getsize(session_file)
        logger.info(f"Session file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Session file is empty. Please log in again.")
            return
    else:
        logger.error(f"Session file does not exist: {session_file}")
        print("No Telegram session found. Please log in first.")
        return
    
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        await client.connect()
        
        # Check if authorized
        if await client.is_user_authorized():
            logger.info("Successfully authorized with Telegram")
            
            # Get the current user
            me = await client.get_me()
            logger.info(f"Logged in as: {me.first_name} {me.last_name if me.last_name else ''} (@{me.username})")
            logger.info(f"User ID: {me.id}")
            
            # Try to get some dialogs to verify connection
            try:
                logger.info("Fetching dialogs...")
                dialogs = await client.get_dialogs(limit=5)
                logger.info(f"Successfully fetched {len(dialogs)} dialogs")
                
                for i, dialog in enumerate(dialogs):
                    logger.info(f"Dialog {i+1}: {dialog.name} (ID: {dialog.id})")
                
                print(f"Telegram connection is working properly.")
                print(f"Logged in as: {me.first_name} {me.last_name if me.last_name else ''} (@{me.username})")
                print(f"Successfully fetched {len(dialogs)} dialogs")
            except Exception as e:
                logger.error(f"Error fetching dialogs: {e}")
                print(f"Error fetching dialogs: {e}")
        else:
            logger.error("Not authorized with Telegram")
            print("Not authorized with Telegram. Please log in again.")
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}")
        print(f"Error connecting to Telegram: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_telegram_connection()) 