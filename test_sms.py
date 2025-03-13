#!/usr/bin/env python3
"""
Test SMS Sending
This script tests the SMS sending functionality using the configured SMS provider.
"""

import os
import logging
from dotenv import load_dotenv
from sms_providers import get_sms_provider

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Your phone number to receive SMS
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')

# Check if required environment variables are set
if not YOUR_PHONE_NUMBER:
    logger.error("Missing required environment variable: YOUR_PHONE_NUMBER")
    logger.error("Please create a .env file with this variable or set it in your environment.")
    exit(1)

def send_test_sms():
    """Send a test SMS using the configured SMS provider."""
    try:
        # Initialize SMS provider
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return False
        
        # Send the test message
        message_text = f"This is a test message from your Telegram to SMS Forwarder using {provider_name}."
        success = sms_provider.send_sms(message_text, YOUR_PHONE_NUMBER)
        
        if success:
            logger.info(f"Test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({YOUR_PHONE_NUMBER}) for the test message.")
        else:
            logger.error(f"Failed to send SMS via {provider_name}")
        
        return success
    except ValueError as e:
        logger.error(f"Failed to initialize SMS provider: {e}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing SMS sending functionality...")
    success = send_test_sms()
    
    if success:
        logger.info("SMS test completed successfully!")
    else:
        logger.error("SMS test failed. Please check your SMS provider credentials and try again.")
        exit(1) 