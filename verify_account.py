#!/usr/bin/env python3
"""
Verify Telegram Account
This script verifies that we can authenticate with your Telegram account.
"""

import os
import asyncio
import logging
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

async def main():
    """Main function to verify account."""
    print("=== TELEGRAM ACCOUNT VERIFICATION ===")
    
    # Create client
    client = TelegramClient('verify_session', API_ID, API_HASH)
    
    # Connect to Telegram
    print("Connecting to Telegram...")
    await client.connect()
    
    # Check if already authorized
    if await client.is_user_authorized():
        print("Already authorized, getting account info...")
    else:
        # Get phone number
        phone = input("Please enter your phone number with country code (e.g., +1234567890): ")
        
        # Send code request
        print(f"Sending code request to {phone}...")
        await client.send_code_request(phone)
        
        # Get verification code
        code = input("Please enter the verification code sent to your Telegram app: ")
        
        # Sign in
        print("Signing in...")
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            if "2FA" in str(e) or "password" in str(e).lower():
                password = input("Please enter your 2FA password: ")
                await client.sign_in(password=password)
            else:
                print(f"Error during sign in: {e}")
                return
    
    # Get account info
    me = await client.get_me()
    print("\n=== ACCOUNT INFORMATION ===")
    print(f"Name: {me.first_name} {me.last_name if me.last_name else ''}")
    print(f"Username: {me.username or 'None'}")
    print(f"Phone: {me.phone}")
    print(f"User ID: {me.id}")
    
    # Get dialogs (chats)
    print("\nFetching your chats...")
    dialogs = await client.get_dialogs(limit=5)
    print(f"Found {len(dialogs)} chats")
    
    # Print first few chats
    print("\nFirst few chats:")
    for i, dialog in enumerate(dialogs, 1):
        entity = dialog.entity
        name = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or 'Unknown'
        print(f"{i}. {name}")
    
    # Disconnect
    await client.disconnect()
    print("\n✅ Verification complete! Your Telegram account is accessible.")

if __name__ == "__main__":
    asyncio.run(main()) 