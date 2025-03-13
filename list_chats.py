#!/usr/bin/env python3
"""
List Telegram Chats
This script lists all your Telegram chats to help you configure which ones to monitor.
"""

import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
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

# Check if required environment variables are set
if not API_ID or not API_HASH:
    logger.error("Missing required environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH")
    logger.error("Please create a .env file with these variables or set them in your environment.")
    exit(1)

# Initialize Telegram client
client = TelegramClient('telegram_to_sms_session', API_ID, API_HASH)

async def main():
    """Main function to list all chats."""
    logger.info("Starting Telegram Chat Lister...")
    
    # Connect to Telegram
    await client.start()
    
    me = await client.get_me()
    logger.info(f"Logged in as {me.first_name} ({me.username or me.id})")
    
    # Get all dialogs (chats)
    logger.info("Fetching your chats...")
    dialogs = await client.get_dialogs()
    
    # Print header
    print("\n{:<5} {:<20} {:<15} {:<40}".format("Type", "Username/ID", "Chat Type", "Name"))
    print("-" * 80)
    
    # Print each chat
    for i, dialog in enumerate(dialogs, 1):
        entity = dialog.entity
        
        # Determine chat type
        if isinstance(entity, User):
            chat_type = "User"
        elif isinstance(entity, Chat):
            chat_type = "Group"
        elif isinstance(entity, Channel):
            if entity.broadcast:
                chat_type = "Channel"
            else:
                chat_type = "Supergroup"
        else:
            chat_type = "Unknown"
        
        # Get username or ID
        if hasattr(entity, 'username') and entity.username:
            username_or_id = entity.username
        else:
            username_or_id = entity.id
        
        # Get name
        if isinstance(entity, User):
            if entity.first_name and entity.last_name:
                name = f"{entity.first_name} {entity.last_name}"
            else:
                name = entity.first_name or "Unknown"
        else:
            name = entity.title or "Unknown"
        
        # Print chat info
        print("{:<5} {:<20} {:<15} {:<40}".format(
            i, 
            username_or_id, 
            chat_type, 
            name
        ))
    
    print("\n" + "-" * 80)
    print("To monitor specific chats, add their usernames or IDs to the MONITORED_CHATS list in config.py")
    print("Example: MONITORED_CHATS = ['username1', 'username2', 123456789]")
    print("Or set FORWARD_ALL_CHATS = True to monitor all chats")
    
    # Disconnect
    await client.disconnect()
    logger.info("Done!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1) 