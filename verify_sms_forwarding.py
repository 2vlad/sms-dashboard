#!/usr/bin/env python3
"""
Verify SMS Forwarding
This script verifies that the SMS forwarding functionality is working correctly.
"""

import os
import sys
import logging
import sqlite3
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from sms_providers import get_sms_provider

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

# Database path
DATABASE_PATH = 'forwarder.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_phone_number(user_id):
    """Get the phone number for a user."""
    conn = get_db_connection()
    user = conn.execute('SELECT phone_number FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user and user['phone_number']:
        return user['phone_number']
    else:
        return None

def get_service_status(user_id):
    """Get the service status for a user."""
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM service_status WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if service:
        return dict(service)
    else:
        return {
            'status': 'unknown',
            'last_check': 0,
            'error_message': None,
            'pid': None
        }

async def verify_sms_forwarding():
    """Verify that the SMS forwarding functionality is working correctly."""
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    # Connect to Telegram
    await client.connect()
    
    # Check if authorized
    if not await client.is_user_authorized():
        logger.error("Not authorized. Please log in first.")
        return
    
    # Get the user info
    me = await client.get_me()
    user_id = me.id
    logger.info(f"Logged in as {me.first_name} ({me.username or me.id})")
    
    # Get the user's phone number
    phone_number = get_user_phone_number(user_id)
    if not phone_number:
        logger.error("No phone number found for user. Please set your phone number in the web interface.")
        return
    
    logger.info(f"User phone number: {phone_number}")
    
    # Check the service status
    status = get_service_status(user_id)
    logger.info(f"Service status: {status['status']}")
    
    if status['status'] != 'running':
        logger.warning("Forwarder service is not running. Please start it from the web interface.")
    
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
        test_message = f"This is a test message from the SMS Forwarding verification script."
        logger.info(f"Sending test SMS to {phone_number}...")
        success = sms_provider.send_sms(test_message, phone_number)
        
        if success:
            logger.info(f"Test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({phone_number}) for the test message.")
        else:
            logger.error(f"Failed to send SMS via {provider_name}")
            return
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        return
    
    # Send a message to yourself to test
    logger.info("Sending a test message to yourself...")
    await client.send_message('me', 'Test message from SMS Forwarding verification script')
    logger.info("Test message sent. If the forwarder is running, you should receive an SMS.")
    
    # Wait for a moment
    logger.info("Waiting for 10 seconds...")
    await asyncio.sleep(10)
    
    # Disconnect
    await client.disconnect()
    logger.info("Verification completed.")

if __name__ == "__main__":
    asyncio.run(verify_sms_forwarding()) 