#!/usr/bin/env python3
"""
Test Forwarder
This script tests the Telegram to SMS forwarder functionality directly.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from sms_providers import get_sms_provider
import config

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

# Create a directory for Telegram sessions
TELEGRAM_SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_sessions')
os.makedirs(TELEGRAM_SESSIONS_DIR, exist_ok=True)
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')

# Get the phone number from environment variables
PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')
if not PHONE_NUMBER:
    logger.error("YOUR_PHONE_NUMBER environment variable is not set")
    sys.exit(1)

async def test_forwarder():
    """Test the Telegram to SMS forwarder functionality."""
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    # Connect to Telegram
    await client.connect()
    
    # Check if authorized
    if not await client.is_user_authorized():
        logger.error("Not authorized. Please log in first.")
        return
    
    # Initialize SMS provider
    try:
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return
        
        # Send a test message
        test_message = f"This is a test message from your Telegram to SMS Forwarder using {provider_name}."
        logger.info(f"Sending test SMS to {PHONE_NUMBER}...")
        success = sms_provider.send_sms(test_message, PHONE_NUMBER)
        
        if success:
            logger.info(f"Test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({PHONE_NUMBER}) for the test message.")
        else:
            logger.error(f"Failed to send SMS via {provider_name}")
            return
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        return
    
    # Print configuration
    logger.info("Forwarder configuration:")
    logger.info(f"FORWARD_ALL_CHATS: {config.FORWARD_ALL_CHATS}")
    logger.info(f"ONLY_NON_MUTED_CHATS: {config.ONLY_NON_MUTED_CHATS}")
    logger.info(f"FORWARD_MEDIA: {config.FORWARD_MEDIA}")
    logger.info(f"FORWARD_OWN_MESSAGES: {config.FORWARD_OWN_MESSAGES}")
    
    # Get me
    me = await client.get_me()
    logger.info(f"Logged in as {me.first_name} ({me.username or me.id})")
    
    # Send a message to yourself to test
    logger.info("Sending a test message to yourself...")
    await client.send_message('me', 'Test message from Telegram to SMS Forwarder')
    logger.info("Test message sent. Check if you receive an SMS.")
    
    # Wait for a moment
    logger.info("Waiting for 10 seconds...")
    await asyncio.sleep(10)
    
    # Disconnect
    await client.disconnect()
    logger.info("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_forwarder()) 