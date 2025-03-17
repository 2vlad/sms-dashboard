#!/usr/bin/env python3
"""
Check SMS Provider
This script checks the status and capabilities of the SMS provider.
"""

import os
import sys
import logging
import time
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

def check_sms_provider():
    """Check the SMS provider status and capabilities."""
    try:
        # Initialize SMS provider
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return
        
        logger.info(f"SMS provider credentials verified successfully")
        
        # Get the phone number from environment or input
        phone_number = os.getenv('TEST_PHONE_NUMBER')
        if not phone_number:
            phone_number = input("Enter a phone number to test SMS sending (e.g., +79999892400): ")
        
        logger.info(f"Using phone number: {phone_number}")
        
        # Send a test SMS
        test_message = f"Test message from check_sms_provider.py at {time.strftime('%H:%M:%S')}"
        logger.info(f"Sending test SMS to {phone_number}...")
        
        # Try to send the SMS
        success = sms_provider.send_sms(test_message, phone_number)
        
        if success:
            logger.info(f"Test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({phone_number}) for the test message.")
        else:
            logger.error(f"Failed to send SMS via {provider_name}")
        
        # Wait for a minute and try again to test rate limiting
        logger.info("Waiting for 60 seconds to test rate limiting...")
        time.sleep(60)
        
        # Send another test SMS
        test_message = f"Second test message from check_sms_provider.py at {time.strftime('%H:%M:%S')}"
        logger.info(f"Sending second test SMS to {phone_number}...")
        
        # Try to send the SMS
        success = sms_provider.send_sms(test_message, phone_number)
        
        if success:
            logger.info(f"Second test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({phone_number}) for the test message.")
        else:
            logger.error(f"Failed to send second SMS via {provider_name}")
        
    except Exception as e:
        logger.error(f"Error checking SMS provider: {e}")

if __name__ == "__main__":
    check_sms_provider() 