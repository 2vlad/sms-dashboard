#!/usr/bin/env python3
"""
Verify SMS Provider
This script verifies and tests different SMS providers.
"""

import os
import logging
import argparse
from dotenv import load_dotenv
from sms_providers import get_sms_provider, TwilioProvider, SMSCProvider, MessageBirdProvider, VonageProvider

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def verify_provider(provider_name=None):
    """Verify a specific SMS provider or the default one."""
    try:
        # Initialize SMS provider
        sms_provider = get_sms_provider(provider_name)
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        
        print(f"\n=== {provider_name.upper()} PROVIDER VERIFICATION ===")
        
        # Verify credentials
        print(f"Verifying {provider_name} credentials...")
        if sms_provider.verify_credentials():
            print(f"✅ {provider_name} credentials verified successfully!")
        else:
            print(f"❌ {provider_name} credentials verification failed.")
            return False
        
        # Ask if user wants to send a test message
        print(f"\nWould you like to send a test SMS using {provider_name}? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            # Get the phone number
            your_phone = os.getenv('YOUR_PHONE_NUMBER')
            if not your_phone:
                print("Please enter your phone number to receive the test SMS:")
                your_phone = input("Phone number (with country code, e.g., +1234567890): ")
            
            # Send the test message
            print(f"Sending test SMS to {your_phone}...")
            message_text = f"This is a test message from your Telegram to SMS Forwarder using {provider_name}."
            success = sms_provider.send_sms(message_text, your_phone)
            
            if success:
                print(f"✅ Test SMS sent successfully via {provider_name}!")
                print(f"Check your phone ({your_phone}) for the test message.")
            else:
                print(f"❌ Failed to send SMS via {provider_name}.")
                return False
        
        return True
    except ValueError as e:
        print(f"❌ Failed to initialize {provider_name} provider: {e}")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return False

def setup_provider(provider_name):
    """Guide the user through setting up a specific SMS provider."""
    print(f"\n=== SETTING UP {provider_name.upper()} ===")
    
    if provider_name == 'twilio':
        print("To use Twilio, you need the following information:")
        print("1. Account SID (from your Twilio dashboard)")
        print("2. Auth Token (from your Twilio dashboard)")
        print("3. Twilio Phone Number (purchased from Twilio)")
        print("\nAdd the following to your .env file:")
        print("TWILIO_ACCOUNT_SID=your_account_sid")
        print("TWILIO_AUTH_TOKEN=your_auth_token")
        print("TWILIO_PHONE_NUMBER=your_twilio_phone_number")
        print("SMS_PROVIDER=twilio")
    
    elif provider_name == 'smsc':
        print("To use SMSC.ru, you need the following information:")
        print("1. Login (your SMSC.ru username)")
        print("2. Password (your SMSC.ru password)")
        print("3. Sender ID (optional, defaults to 'SMS')")
        print("\nAdd the following to your .env file:")
        print("SMSC_LOGIN=your_login")
        print("SMSC_PASSWORD=your_password")
        print("SMSC_SENDER=your_sender_id  # Optional")
        print("SMS_PROVIDER=smsc")
        print("\nYou can sign up at https://smsc.ru/")
    
    elif provider_name == 'messagebird':
        print("To use MessageBird, you need the following information:")
        print("1. API Key (from your MessageBird dashboard)")
        print("2. Originator (your sender ID or phone number)")
        print("\nAdd the following to your .env file:")
        print("MESSAGEBIRD_API_KEY=your_api_key")
        print("MESSAGEBIRD_ORIGINATOR=your_originator  # Optional, defaults to 'SMS'")
        print("SMS_PROVIDER=messagebird")
        print("\nYou can sign up at https://www.messagebird.com/")
    
    elif provider_name == 'vonage':
        print("To use Vonage (formerly Nexmo), you need the following information:")
        print("1. API Key (from your Vonage dashboard)")
        print("2. API Secret (from your Vonage dashboard)")
        print("3. From Number (your Vonage phone number or sender ID)")
        print("\nAdd the following to your .env file:")
        print("VONAGE_API_KEY=your_api_key")
        print("VONAGE_API_SECRET=your_api_secret")
        print("VONAGE_FROM_NUMBER=your_from_number  # Optional, defaults to 'SMS'")
        print("SMS_PROVIDER=vonage")
        print("\nYou can sign up at https://www.vonage.com/")

def list_providers():
    """List all available SMS providers with their features and pricing."""
    print("\n=== AVAILABLE SMS PROVIDERS ===")
    
    print("\n1. SMSC.ru")
    print("   - Russian provider with good rates for Russian numbers")
    print("   - Simple API with good documentation")
    print("   - Website: https://smsc.ru/")
    print("   - Best for: Russian phone numbers")
    
    print("\n2. MessageBird")
    print("   - Global provider with competitive rates")
    print("   - Advanced features and good API")
    print("   - Website: https://www.messagebird.com/")
    print("   - Best for: International coverage")
    
    print("\n3. Vonage (formerly Nexmo)")
    print("   - Global provider with good coverage")
    print("   - Enterprise-grade features")
    print("   - Website: https://www.vonage.com/")
    print("   - Best for: Enterprise applications")
    
    print("\n4. Twilio")
    print("   - Popular global provider")
    print("   - Extensive features but can be expensive")
    print("   - Website: https://www.twilio.com/")
    print("   - Best for: Developer-friendly API")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Verify and test SMS providers')
    parser.add_argument('--provider', choices=['twilio', 'smsc', 'messagebird', 'vonage'], 
                        help='Specify the SMS provider to verify')
    parser.add_argument('--setup', choices=['twilio', 'smsc', 'messagebird', 'vonage'], 
                        help='Get setup instructions for a specific provider')
    parser.add_argument('--list', action='store_true', 
                        help='List all available SMS providers')
    
    args = parser.parse_args()
    
    if args.list:
        list_providers()
        return
    
    if args.setup:
        setup_provider(args.setup)
        return
    
    if args.provider:
        verify_provider(args.provider)
    else:
        # If no provider specified, check the environment variable
        provider_name = os.getenv('SMS_PROVIDER', 'twilio').lower()
        print(f"Using provider from environment: {provider_name}")
        verify_provider(provider_name)

if __name__ == "__main__":
    main() 