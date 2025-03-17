#!/usr/bin/env python3
"""
Start Telegram to SMS Forwarder
This script starts the Telegram to SMS forwarder service.
"""

import os
import logging
import asyncio
import signal
import sys
import time
import threading
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel
from dotenv import load_dotenv
import config
from sms_providers import get_sms_provider
from datetime import datetime
from message_summarizer import MessageSummarizer  # Import the message summarizer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    handlers=[
        logging.FileHandler("forwarder.log"),
        logging.StreamHandler()
    ]
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

# Global flag to control the forwarder
running = True

# Check if all required environment variables are set
required_vars = [
    ('TELEGRAM_API_ID', API_ID),
    ('TELEGRAM_API_HASH', API_HASH),
    ('YOUR_PHONE_NUMBER', YOUR_PHONE_NUMBER)
]

missing_vars = [name for name, value in required_vars if not value]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please create a .env file with these variables or set them in your environment.")
    sys.exit(1)

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
    logger.info(f"Checking if chat {chat_id} should be monitored")
    
    # First, check if we should only monitor non-muted chats
    if config.ONLY_NON_MUTED_CHATS:
        try:
            # Get the dialogs with a higher limit to ensure we find the chat
            dialogs = await client.get_dialogs(limit=200)
            found_dialog = False
            
            for d in dialogs:
                if hasattr(d, 'id') and d.id == chat_id:
                    found_dialog = True
                    # Check if the chat is muted
                    if d.archived or d.notify_settings.mute_until:
                        logger.info(f"Chat {chat_id} is muted, skipping")
                        return False
                    logger.info(f"Chat {chat_id} is not muted")
                    break
                elif hasattr(d, 'entity') and hasattr(d.entity, 'id') and d.entity.id == chat_id:
                    found_dialog = True
                    # Check if the chat is muted
                    if hasattr(d, 'dialog') and hasattr(d.dialog, 'notify_settings') and d.dialog.notify_settings.mute_until:
                        logger.info(f"Chat {chat_id} is muted, skipping")
                        return False
                    logger.info(f"Chat {chat_id} is not muted")
                    break
            
            if not found_dialog:
                logger.warning(f"Dialog for chat {chat_id} not found in the first 200 dialogs")
                # If we can't find the dialog, default to NOT monitoring it for safety
                return False
        except Exception as e:
            logger.error(f"Error checking if chat is muted: {e}")
            # If there's an error, default to NOT monitoring to be safe
            return False
    
    # Then check other monitoring conditions
    if config.FORWARD_ALL_CHATS:
        logger.info(f"FORWARD_ALL_CHATS is enabled, chat {chat_id} will be monitored")
        return True
    
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

async def run_forwarder():
    """Run the Telegram to SMS forwarder."""
    global running
    
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
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        return
    
    # Initialize message summarizer
    # Use configuration options
    if config.ENABLE_MESSAGE_SUMMARIZATION:
        summarizer = MessageSummarizer(
            delay_seconds=config.SUMMARIZATION_DELAY,
            max_messages=config.MAX_SUMMARY_MESSAGES,
            max_summary_length=config.MAX_SMS_LENGTH
        )
        logger.info("Message summarizer initialized")
    else:
        summarizer = None
        logger.info("Message summarization is disabled")
    
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    # Set up automatic reconnection
    client.flood_sleep_threshold = 60  # Sleep for 60 seconds when flood wait occurs
    
    try:
        # Connect to Telegram
        logger.info("Connecting to Telegram...")
        await client.connect()
        
        # Check if authorized
        if not await client.is_user_authorized():
            logger.error("Not authorized. Please log in first.")
            return
        
        # Get the user info
        me = await client.get_me()
        logger.info(f"Logged in as {me.first_name} ({me.username or me.id})")
        
        # Print configuration
        logger.info("Forwarder configuration:")
        logger.info(f"FORWARD_ALL_CHATS: {config.FORWARD_ALL_CHATS}")
        logger.info(f"ONLY_NON_MUTED_CHATS: {config.ONLY_NON_MUTED_CHATS}")
        logger.info(f"FORWARD_MEDIA: {config.FORWARD_MEDIA}")
        logger.info(f"FORWARD_OWN_MESSAGES: {config.FORWARD_OWN_MESSAGES}")
        logger.info(f"MONITORED_CHATS: {config.MONITORED_CHATS}")
        logger.info(f"ENABLE_MESSAGE_SUMMARIZATION: {config.ENABLE_MESSAGE_SUMMARIZATION}")
        if config.ENABLE_MESSAGE_SUMMARIZATION:
            logger.info(f"SUMMARIZATION_DELAY: {config.SUMMARIZATION_DELAY} seconds")
            logger.info(f"MAX_SUMMARY_MESSAGES: {config.MAX_SUMMARY_MESSAGES}")
        
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
                
                # Check if the chat is muted
                is_muted = False
                if config.ONLY_NON_MUTED_CHATS:
                    try:
                        dialogs = await client.get_dialogs(limit=200)
                        for d in dialogs:
                            if (hasattr(d, 'id') and d.id == chat_id) or \
                               (hasattr(d, 'entity') and hasattr(d.entity, 'id') and d.entity.id == chat_id):
                                if d.archived or d.notify_settings.mute_until:
                                    is_muted = True
                                break
                    except Exception as e:
                        logger.error(f"Error checking mute status: {e}")
                
                # Skip muted chats entirely
                if is_muted:
                    logger.info(f"Skipping message from muted chat {chat_name}")
                    return
                
                # For non-muted chats, either send immediately or add to summarizer based on config
                if config.ENABLE_MESSAGE_SUMMARIZATION and summarizer:
                    logger.info(f"Adding message from non-muted chat {chat_name} to summarizer")
                    summarizer.add_message(chat_id, message_text, sender_name)
                    return
                
                # Format the message for SMS
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
        
        # Send a notification that the forwarder has started
        notification = f"Telegram to SMS Forwarder started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"Sending startup notification: {notification}")
        sms_provider.send_sms(notification, YOUR_PHONE_NUMBER)
        
        # Log that we're starting to listen for messages
        logger.info(f"Started listening for messages")
        logger.info("Press Ctrl+C to stop")
        
        # Set up a keep-alive mechanism
        async def keep_alive():
            while running:
                try:
                    # Check if we're still connected
                    if not client.is_connected():
                        logger.warning("Connection lost, reconnecting...")
                        await client.connect()
                        
                    # Send a ping every 5 minutes to keep the connection alive
                    if client.is_connected():
                        # Use get_me() as a ping since TelegramClient doesn't have a ping method
                        await client.get_me()
                        logger.debug("Ping sent to keep connection alive")
                    
                    # Wait for 5 minutes
                    await asyncio.sleep(300)
                except Exception as e:
                    logger.error(f"Error in keep-alive: {e}")
                    await asyncio.sleep(30)  # Wait a bit before retrying
        
        # Set up a task to process summarized messages
        async def process_summaries():
            if not config.ENABLE_MESSAGE_SUMMARIZATION or not summarizer:
                return
                
            while running:
                try:
                    # Check all chats with pending messages
                    for chat_id, count in [(chat_id, summarizer.get_pending_messages_count(chat_id)) 
                                          for chat_id in summarizer.chat_messages.keys()]:
                        if count > 0:
                            logger.debug(f"Chat {chat_id} has {count} pending messages")
                            
                            # If the timer has expired, the summarizer will handle it
                            # We don't need to do anything here
                            
                            # If a summary is generated by the timer, it will call the callback
                            # which will send the SMS
                    
                    # Wait for 30 seconds before checking again
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error(f"Error in summary processor: {e}")
                    await asyncio.sleep(30)  # Wait a bit before retrying
        
        # Function to send a summary SMS
        def send_summary_sms(chat_id, summary_text):
            if not summary_text:
                return
            
            try:
                # Get the chat name
                chat_name = "Unknown Chat"
                # We'll use a generic name since we can't easily get the chat entity here
                
                # Format the message for SMS
                timestamp = datetime.now().strftime("%H:%M:%S")
                sms_text = f"[{timestamp}] Summary from {chat_name}: {summary_text}"
                
                # Truncate message if it's too long
                if len(sms_text) > config.MAX_SMS_LENGTH:
                    sms_text = sms_text[:config.MAX_SMS_LENGTH - 3] + "..."
                
                # Send SMS and get success status
                logger.info(f"Sending summary SMS to {YOUR_PHONE_NUMBER}: {sms_text[:30]}...")
                success = sms_provider.send_sms(sms_text, YOUR_PHONE_NUMBER)
                
                if success:
                    logger.info(f"Summary SMS sent successfully to {YOUR_PHONE_NUMBER}")
                else:
                    logger.error(f"Failed to send summary SMS to {YOUR_PHONE_NUMBER}")
            except Exception as e:
                logger.error(f"Failed to send summary SMS: {e}")
        
        # Set up a callback for when summaries are generated
        def summary_callback(chat_id):
            # This will be called when the timer expires for a chat
            summary = summarizer.process_chat_messages(chat_id)
            if summary:
                # We need to run this in the event loop
                asyncio.create_task(client.loop.run_in_executor(None, send_summary_sms, chat_id, summary))
        
        # Register the callback with the summarizer
        if config.ENABLE_MESSAGE_SUMMARIZATION and summarizer:
            for chat_id in summarizer.chat_timers:
                if summarizer.chat_timers[chat_id]:
                    summarizer.chat_timers[chat_id].cancel()
                    summarizer.chat_timers[chat_id] = None
        
        # Start the keep-alive task
        keep_alive_task = asyncio.create_task(keep_alive())
        
        # Start the summary processor task
        summary_processor_task = asyncio.create_task(process_summaries())
        
        # Run the client until disconnected
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping...")
    except Exception as e:
        logger.error(f"Error in forwarder: {e}")
    finally:
        # Set the running flag to False to stop the keep-alive task
        running = False
        
        # Send a notification that the forwarder has stopped
        try:
            notification = f"Telegram to SMS Forwarder stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Sending shutdown notification: {notification}")
            sms_provider.send_sms(notification, YOUR_PHONE_NUMBER)
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
        
        # Disconnect the client
        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting client: {e}")
        
        logger.info("Forwarder stopped")

def signal_handler(sig, frame):
    """Handle signals to gracefully stop the forwarder."""
    global running
    logger.info(f"Received signal {sig}, stopping...")
    running = False
    sys.exit(0)

async def main():
    """Main function with automatic restart."""
    global running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Telegram to SMS Forwarder with automatic restart...")
    
    # Run the forwarder with automatic restart
    while running:
        try:
            await run_forwarder()
            
            # If we get here, the forwarder has stopped
            if running:
                logger.warning("Forwarder stopped unexpectedly, restarting in 30 seconds...")
                await asyncio.sleep(30)
            else:
                logger.info("Forwarder stopped by user request")
                break
        except Exception as e:
            logger.error(f"Unhandled exception in forwarder: {e}")
            logger.warning("Restarting forwarder in 30 seconds...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 