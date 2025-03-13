#!/usr/bin/env python3
"""
Run Telegram to SMS Forwarder
This script runs the Telegram to SMS forwarder using the existing session file.
"""

import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import config
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if config.DEBUG else logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(message_text):
    """Send an SMS using Twilio."""
    # Truncate message if it's too long
    if len(message_text) > config.MAX_SMS_LENGTH:
        message_text = message_text[:config.MAX_SMS_LENGTH - 3] + "..."
    
    try:
        message = twilio_client.messages.create(
            body=message_text,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_PHONE_NUMBER
        )
        logger.info(f"SMS sent successfully: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS: {e}")
        return False

def get_display_name(entity):
    """Get a display name for a user, chat, or channel."""
    if entity is None:
        return "Unknown"
    
    if isinstance(entity, User):
        if entity.first_name and entity.last_name:
            return f"{entity.first_name} {entity.last_name}"
        return entity.first_name or entity.username or str(entity.id)
    
    if isinstance(entity, (Chat, Channel)):
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
    # First, check if we should only monitor non-muted chats
    if config.ONLY_NON_MUTED_CHATS:
        try:
            # Get the dialog for this chat
            dialog = await client.get_dialogs()
            for d in dialog:
                if d.entity.id == chat_id:
                    # Check if the chat is muted
                    if d.dialog.notify_settings.mute_until:
                        logger.debug(f"Skipping muted chat: {chat_id}")
                        return False
                    break
        except Exception as e:
            logger.error(f"Error checking mute status: {e}")
    
    # Then check other monitoring conditions
    if config.FORWARD_ALL_CHATS:
        return True
    
    if not config.MONITORED_CHATS:
        return False
    
    # Check if chat_id is in the monitored chats list
    if chat_id in config.MONITORED_CHATS:
        return True
    
    # If chat_id is numeric but monitored chats contains usernames
    try:
        entity = await client.get_entity(chat_id)
        if hasattr(entity, 'username') and entity.username in config.MONITORED_CHATS:
            return True
    except Exception as e:
        logger.error(f"Error checking entity: {e}")
    
    return False

async def main():
    """Main function to run the forwarder."""
    print("=== TELEGRAM TO SMS FORWARDER ===")
    
    # Create client using the existing session file
    client = TelegramClient('verify_session', API_ID, API_HASH)
    
    # Connect to Telegram
    print("Connecting to Telegram...")
    await client.connect()
    
    # Check if authorized
    if not await client.is_user_authorized():
        print("❌ Not authorized. Please run verify_account.py first.")
        return
    
    # Get account info
    me = await client.get_me()
    print(f"✅ Connected as {me.first_name} {me.last_name if me.last_name else ''} (@{me.username or 'None'})")
    
    # Register event handler for new messages
    @client.on(events.NewMessage)
    async def handle_new_message(event):
        # Get the chat where the message was sent
        chat = await event.get_chat()
        chat_id = event.chat_id
        
        # Skip if this chat is not monitored
        if not await is_monitored_chat(client, chat_id):
            logger.debug(f"Skipping message from non-monitored chat: {chat_id}")
            return
        
        # Skip own messages if configured to do so
        if event.out and not config.FORWARD_OWN_MESSAGES:
            logger.debug("Skipping own message")
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
                logger.debug("Skipping media message")
                return
            
            message_text = event.message.text
        
        # Skip empty messages
        if not message_text:
            logger.debug("Skipping empty message")
            return
        
        # Format the message for SMS
        timestamp = datetime.now().strftime("%H:%M:%S")
        if config.INCLUDE_SENDER_NAME:
            sms_text = f"[{timestamp}] {chat_name} - {sender_name}: {message_text}"
        else:
            sms_text = f"[{timestamp}] {chat_name}: {message_text}"
        
        # Log the message
        print(f"📱 Forwarding message from {chat_name}")
        
        # Send the SMS
        send_sms(sms_text)
    
    # Log configuration information
    if config.ONLY_NON_MUTED_CHATS:
        print("📱 Only forwarding messages from non-muted chats")
    elif config.FORWARD_ALL_CHATS:
        print("📱 Forwarding messages from all chats")
    else:
        print(f"📱 Forwarding messages from {len(config.MONITORED_CHATS)} monitored chats")
    
    print("\n🔄 Listening for new messages... (Press Ctrl+C to stop)")
    
    # Keep the script running
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping Telegram to SMS Forwarder...")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1) 