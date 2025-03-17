#!/usr/bin/env python3
"""
Test Telegram to SMS Forwarding
This script tests the complete Telegram to SMS forwarding process.
"""

import os
import logging
import asyncio
import time
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel
from dotenv import load_dotenv
import config
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

# Your phone number to receive SMS
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')

# Web login session path
WEB_LOGIN_SESSION_PATH = 'telegram_sessions/web_login_session'

def get_display_name(entity):
    """Get a display name for a user, chat, or channel."""
    if isinstance(entity, User):
        if entity.first_name and entity.last_name:
            return f"{entity.first_name} {entity.last_name}"
        elif entity.first_name:
            return entity.first_name
        elif entity.username:
            return entity.username
        else:
            return f"User {entity.id}"
    elif isinstance(entity, (Chat, Channel)):
        if entity.title:
            return entity.title
        elif getattr(entity, 'username', None):
            return entity.username
        else:
            return f"Chat {entity.id}"
    else:
        return "Unknown"

async def is_monitored_chat(client, chat_id):
    """Check if a chat should be monitored."""
    # If FORWARD_ALL_CHATS is True, monitor all chats
    if config.FORWARD_ALL_CHATS:
        return True
    
    # If ONLY_NON_MUTED_CHATS is True, only monitor non-muted chats
    if config.ONLY_NON_MUTED_CHATS:
        # Get the dialog for this chat
        dialog = await client.get_dialogs()
        for d in dialog:
            if d.id == chat_id:
                # Check if the chat is muted
                return not d.archived and not d.notify_settings.mute_until
    
    # Otherwise, check if the chat is in MONITORED_CHATS
    for monitored in config.MONITORED_CHATS:
        if isinstance(monitored, int) and monitored == chat_id:
            return True
        elif isinstance(monitored, str):
            # Get the entity for this chat
            try:
                entity = await client.get_entity(monitored)
                if entity.id == chat_id:
                    return True
            except Exception as e:
                logger.error(f"Error getting entity for {monitored}: {e}")
    
    return False

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

async def test_forwarding():
    """Test the complete Telegram to SMS forwarding process."""
    logger.info("Testing Telegram to SMS forwarding...")
    
    # Initialize SMS provider
    try:
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return False
        
        logger.info(f"SMS provider credentials verified successfully")
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        return False
    
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
        
        # Register event handler for new messages
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                # Get the chat where the message was sent
                chat = await event.get_chat()
                chat_id = event.chat_id
                
                # Log the message
                logger.info(f"Received message from chat: {chat_id} ({get_display_name(chat)})")
                
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
                
                # Send the SMS
                try:
                    # Truncate message if it's too long
                    if len(sms_text) > config.MAX_SMS_LENGTH:
                        sms_text = sms_text[:config.MAX_SMS_LENGTH - 3] + "..."
                    
                    # Send SMS and get success status
                    logger.info(f"Sending SMS to {YOUR_PHONE_NUMBER}: {sms_text[:30]}...")
                    success = sms_provider.send_sms(sms_text, YOUR_PHONE_NUMBER)
                    
                    if success:
                        logger.info(f"SMS sent successfully to {YOUR_PHONE_NUMBER}")
                    else:
                        logger.error(f"Failed to send SMS to {YOUR_PHONE_NUMBER}")
                        
                except Exception as e:
                    logger.error(f"Failed to send SMS: {e}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
        
        # Send a test message to yourself
        logger.info("Sending a test message to yourself...")
        await client.send_message('me', 'Test message from test_forwarding.py')
        logger.info("Test message sent. You should receive an SMS shortly.")
        
        # Wait for the message to be processed
        logger.info("Waiting for the message to be processed...")
        await asyncio.sleep(10)
        
        return True
    except Exception as e:
        logger.error(f"Error testing forwarding: {e}")
        return False
    finally:
        # Disconnect the client
        await client.disconnect()

async def main():
    """Main function to run the script."""
    if await test_forwarding():
        logger.info("Forwarding test completed successfully")
    else:
        logger.error("Forwarding test failed")

if __name__ == "__main__":
    asyncio.run(main()) 