#!/usr/bin/env python3
"""
Test Telegram Authorization
This script tests the Telegram client authorization.
"""

import os
import logging
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

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

# Web login session path
WEB_LOGIN_SESSION_PATH = 'telegram_sessions/web_login_session'

async def test_telegram_auth():
    """Test the Telegram client authorization."""
    logger.info("Testing Telegram client authorization...")
    
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        await client.connect()
        
        # Check if authorized
        if not await client.is_user_authorized():
            logger.error("Not authorized. Please log in first.")
            return False
        
        # Get the user info
        me = await client.get_me()
        logger.info(f"Logged in as {me.first_name} ({me.username or me.id})")
        
        # Send a test message to yourself
        logger.info("Sending a test message to yourself...")
        await client.send_message('me', 'Test message from test_telegram_auth.py')
        logger.info("Test message sent successfully!")
        
        return True
    except Exception as e:
        logger.error(f"Error testing Telegram authorization: {e}")
        return False
    finally:
        # Disconnect the client
        await client.disconnect()

async def main():
    """Main function to run the script."""
    if await test_telegram_auth():
        logger.info("Telegram authorization test completed successfully")
    else:
        logger.error("Telegram authorization test failed")

if __name__ == "__main__":
    asyncio.run(main()) 