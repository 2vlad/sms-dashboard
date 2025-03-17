#!/usr/bin/env python3
"""
Debug Forwarder with Log
This script helps debug the Telegram to SMS forwarder service and logs all output to a file.
"""

import os
import sys
import logging
import sqlite3
import asyncio
import time
from dotenv import load_dotenv
from telethon import TelegramClient, events
from sms_providers import get_sms_provider
import config

# Configure logging to file
logging.basicConfig(
    filename='debug_forwarder.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

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

def update_service_status(user_id, status, error_message=None, pid=None):
    """Update the service status for a user."""
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM service_status WHERE user_id = ?', (user_id,)).fetchone()
    
    if service:
        # Convert to dictionary if it's a sqlite3.Row object
        service_dict = dict(service) if service else {}
        
        # Check if pid is None and service has a pid
        if pid is None and service_dict.get('pid') is not None:
            pid = service_dict['pid']
        
        conn.execute(
            'UPDATE service_status SET status = ?, last_check = ?, error_message = ?, pid = ? WHERE user_id = ?',
            (status, int(time.time()), error_message, pid, user_id)
        )
    else:
        conn.execute(
            'INSERT INTO service_status (user_id, status, last_check, error_message, pid) VALUES (?, ?, ?, ?, ?)',
            (user_id, status, int(time.time()), error_message, pid)
        )
    
    conn.commit()
    conn.close()

def save_message(user_id, chat_name, sender_name, message_text, delivered):
    """Save a forwarded message to the database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO messages (user_id, chat_name, sender_name, message_text, delivered, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, chat_name, sender_name, message_text, delivered, int(time.time()))
    )
    conn.commit()
    conn.close()

def save_telegram_message(user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded=True):
    """Save a Telegram message to the database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT OR IGNORE INTO telegram_messages (user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded)
    )
    conn.commit()
    conn.close()

def get_display_name(entity):
    """Get a display name for a user, chat, or channel."""
    if entity is None:
        return "Unknown"
    
    if hasattr(entity, 'first_name'):
        if hasattr(entity, 'last_name') and entity.last_name:
            return f"{entity.first_name} {entity.last_name}"
        return entity.first_name or entity.username or str(entity.id)
    
    if hasattr(entity, 'title'):
        return entity.title or entity.username or str(entity.id)
    
    return str(entity.id)

def get_media_type(event):
    """Get the type of media in a message."""
    if event.photo:
        return "Photo"
    elif event.video:
        return "Video"
    elif event.audio:
        return "Audio"
    elif event.voice:
        return "Voice"
    elif event.document:
        return "Document"
    elif event.sticker:
        return "Sticker"
    elif event.gif:
        return "GIF"
    else:
        return "Media"

async def is_monitored_chat(client, chat_id):
    """Check if a chat should be monitored based on config."""
    # Add debug logging
    logger.info(f"Checking if chat {chat_id} should be monitored")
    
    # First, check if we should only monitor non-muted chats
    if config.ONLY_NON_MUTED_CHATS:
        try:
            # Get the dialog for this chat
            logger.info(f"ONLY_NON_MUTED_CHATS is enabled, checking if chat {chat_id} is muted")
            dialogs = await client.get_dialogs(limit=100)  # Increase limit to find more chats
            found_dialog = False
            
            for d in dialogs:
                if d.entity.id == chat_id:
                    found_dialog = True
                    # Check if the chat is muted
                    if d.dialog.notify_settings.mute_until:
                        logger.info(f"Chat {chat_id} is muted, skipping")
                        return False
                    else:
                        logger.info(f"Chat {chat_id} is not muted, will be monitored")
                    break
            
            if not found_dialog:
                logger.warning(f"Dialog for chat {chat_id} not found in the first 100 dialogs")
                # If we can't find the dialog, default to monitoring it
                # This ensures we don't miss messages due to dialog retrieval limitations
                return True
                
        except Exception as e:
            logger.error(f"Error checking mute status: {e}")
            # If there's an error checking mute status, default to monitoring the chat
            # to ensure we don't miss important messages
            return True
    
    # Then check other monitoring conditions
    if config.FORWARD_ALL_CHATS:
        logger.info(f"FORWARD_ALL_CHATS is enabled, chat {chat_id} will be monitored")
        return True
    
    if not config.MONITORED_CHATS:
        logger.info(f"No monitored chats configured, chat {chat_id} will not be monitored")
        return False
    
    # Check if chat_id is in the monitored chats list
    if chat_id in config.MONITORED_CHATS:
        logger.info(f"Chat {chat_id} is in MONITORED_CHATS, will be monitored")
        return True
    
    # If chat_id is numeric but monitored chats contains usernames
    try:
        entity = await client.get_entity(chat_id)
        if hasattr(entity, 'username') and entity.username in config.MONITORED_CHATS:
            logger.info(f"Chat {chat_id} username is in MONITORED_CHATS, will be monitored")
            return True
    except Exception as e:
        logger.error(f"Error checking entity: {e}")
    
    logger.info(f"Chat {chat_id} will not be monitored")
    return False

async def debug_forwarder():
    """Debug the Telegram to SMS forwarder service."""
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
    
    # Initialize SMS provider
    try:
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return
        
        logger.info(f"SMS provider credentials verified successfully")
        
        # Send a test SMS
        test_message = f"This is a test message from debug_forwarder_with_log.py"
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
    
    # Update service status to running
    update_service_status(user_id, 'running', pid=os.getpid())
    logger.info(f"Updated service status to running with PID {os.getpid()}")
    
    # Print configuration
    logger.info("Forwarder configuration:")
    logger.info(f"FORWARD_ALL_CHATS: {config.FORWARD_ALL_CHATS}")
    logger.info(f"ONLY_NON_MUTED_CHATS: {config.ONLY_NON_MUTED_CHATS}")
    logger.info(f"FORWARD_MEDIA: {config.FORWARD_MEDIA}")
    logger.info(f"FORWARD_OWN_MESSAGES: {config.FORWARD_OWN_MESSAGES}")
    
    # Register event handler for new messages
    @client.on(events.NewMessage)
    async def handle_new_message(event):
        try:
            # Add debug logging
            logger.info(f"Received new message event: {event.id}")
            
            # Get the chat where the message was sent
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Add debug logging
            logger.info(f"Message from chat: {chat_id} ({get_display_name(chat)})")
            
            # Skip if this chat is not monitored
            monitored = await is_monitored_chat(client, chat_id)
            logger.info(f"Is chat monitored: {monitored}")
            if not monitored:
                logger.info(f"Skipping message from non-monitored chat: {chat_id}")
                return
            
            # Skip own messages if configured to do so
            if event.out and not config.FORWARD_OWN_MESSAGES:
                logger.info("Skipping own message")
                return
            
            # Get the sender
            sender = await event.get_sender()
            sender_name = "You" if event.out else get_display_name(sender)
            
            # Get chat name
            chat_name = get_display_name(chat)
            
            # Handle media messages
            if event.media and config.FORWARD_MEDIA:
                media_type = get_media_type(event)
                message_text = f"[{media_type}]"
                if event.message.text:
                    message_text += f" {event.message.text}"
            else:
                # Skip media messages if not configured to forward them
                if event.media and not config.FORWARD_MEDIA:
                    logger.info("Skipping media message")
                    return
                
                message_text = event.message.text
            
            # Skip empty messages
            if not message_text:
                logger.info("Skipping empty message")
                return
            
            # Format the message for SMS
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            if config.INCLUDE_SENDER_NAME:
                sms_text = f"[{timestamp}] {chat_name} - {sender_name}: {message_text}"
            else:
                sms_text = f"[{timestamp}] {chat_name}: {message_text}"
            
            # Log the message
            logger.info(f"Forwarding message from {chat_name}: {message_text[:30]}...")
            
            # Save the message to the telegram_messages table
            save_telegram_message(
                user_id,
                event.message.id,
                chat_id,
                chat_name,
                sender_name,
                message_text,
                int(time.time()),
                True  # Mark as forwarded
            )
            
            # Send the SMS
            try:
                # Truncate message if it's too long
                if len(sms_text) > config.MAX_SMS_LENGTH:
                    sms_text = sms_text[:config.MAX_SMS_LENGTH - 3] + "..."
                
                # Send SMS and get success status - note the parameter order: message_text, to_number
                logger.info(f"Sending SMS to {phone_number}: {sms_text[:30]}...")
                success = sms_provider.send_sms(sms_text, phone_number)
                
                # Save the message to the messages table
                save_message(user_id, chat_name, sender_name, message_text, success)
                
                if success:
                    logger.info(f"SMS sent successfully to {phone_number}")
                else:
                    logger.error(f"Failed to send SMS to {phone_number}")
                    
            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")
                # Save the message to the database as failed
                save_message(user_id, chat_name, sender_name, message_text, False)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # Send a test message to yourself
    logger.info("Sending a test message to yourself...")
    await client.send_message('me', 'Test message from debug_forwarder_with_log.py')
    logger.info("Test message sent. You should receive an SMS shortly.")
    
    # Log that we're starting to listen for messages
    logger.info(f"Started listening for messages for user {user_id}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run the client until disconnected
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping...")
    except Exception as e:
        logger.error(f"Error in forwarder: {e}")
    finally:
        # Update service status when disconnected
        update_service_status(user_id, 'stopped')
        logger.info(f"Forwarder stopped for user {user_id}")

if __name__ == "__main__":
    asyncio.run(debug_forwarder()) 