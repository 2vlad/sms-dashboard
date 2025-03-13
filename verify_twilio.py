#!/usr/bin/env python3
"""
Verify Twilio Credentials
This script verifies that your Twilio credentials are working correctly.
"""

import os
import logging
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')

def verify_twilio_credentials():
    """Verify Twilio credentials by checking account info."""
    print("=== TWILIO CREDENTIALS VERIFICATION ===")
    
    # Check if all required environment variables are set
    required_vars = [
        ('TWILIO_ACCOUNT_SID', TWILIO_ACCOUNT_SID),
        ('TWILIO_AUTH_TOKEN', TWILIO_AUTH_TOKEN),
        ('TWILIO_PHONE_NUMBER', TWILIO_PHONE_NUMBER),
        ('YOUR_PHONE_NUMBER', YOUR_PHONE_NUMBER)
    ]
    
    missing_vars = [name for name, value in required_vars if not value]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with these variables.")
        return False
    
    # Initialize Twilio client
    try:
        print(f"Connecting to Twilio with Account SID: {TWILIO_ACCOUNT_SID[:5]}...{TWILIO_ACCOUNT_SID[-5:]}")
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Try to get account info
        print("Fetching account information...")
        account = twilio_client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        
        print("\n=== ACCOUNT INFORMATION ===")
        print(f"Account SID: {account.sid}")
        print(f"Account Name: {account.friendly_name}")
        print(f"Account Status: {account.status}")
        print(f"Account Type: {account.type}")
        
        # Try to get phone number info
        print("\nVerifying phone number...")
        try:
            numbers = twilio_client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE_NUMBER)
            if numbers:
                print(f"✅ Phone number {TWILIO_PHONE_NUMBER} is valid and belongs to your account.")
            else:
                print(f"⚠️ Phone number {TWILIO_PHONE_NUMBER} was not found in your account.")
                print("Please check if the phone number is correct and belongs to your account.")
        except Exception as e:
            print(f"⚠️ Could not verify phone number: {e}")
        
        # Send a test message
        print("\nWould you like to send a test SMS? (y/n)")
        choice = input().lower()
        if choice == 'y':
            try:
                message = twilio_client.messages.create(
                    body="This is a test message from your Telegram to SMS Forwarder.",
                    from_=TWILIO_PHONE_NUMBER,
                    to=YOUR_PHONE_NUMBER
                )
                print(f"✅ Test SMS sent successfully! Message SID: {message.sid}")
                print(f"Check your phone ({YOUR_PHONE_NUMBER}) for the test message.")
            except TwilioRestException as e:
                print(f"❌ Failed to send SMS: {e}")
                return False
        
        print("\n✅ Twilio credentials are valid!")
        return True
    
    except TwilioRestException as e:
        print(f"\n❌ Twilio authentication failed: {e}")
        print("\nPossible solutions:")
        print("1. Check if your Account SID and Auth Token are correct")
        print("2. Make sure your Twilio account is active and not suspended")
        print("3. Check if your Twilio account has sufficient funds")
        print("4. Visit https://www.twilio.com/console to verify your account status")
        return False
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    verify_twilio_credentials() 