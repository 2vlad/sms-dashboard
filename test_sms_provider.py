#!/usr/bin/env python3
"""
Test SMS Provider
This script tests the SMS provider configuration.
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

def test_sms_provider():
    """Test the SMS provider configuration."""
    # Get the phone number from environment
    phone_number = os.getenv('YOUR_PHONE_NUMBER')
    if not phone_number:
        logger.error("No phone number found in environment variables")
        return False
    
    logger.info(f"Using phone number: {phone_number}")
    
    # Initialize SMS provider
    try:
        sms_provider = get_sms_provider()
        provider_name = sms_provider.__class__.__name__.replace('Provider', '')
        logger.info(f"Using SMS provider: {provider_name}")
        
        # Verify credentials
        logger.info("Verifying SMS provider credentials...")
        if not sms_provider.verify_credentials():
            logger.error(f"{provider_name} credentials verification failed")
            return False
        
        logger.info(f"SMS provider credentials verified successfully")
        
        # Send a test SMS
        test_message = f"This is a test message from test_sms_provider.py"
        logger.info(f"Sending test SMS to {phone_number}...")
        success = sms_provider.send_sms(test_message, phone_number)
        
        if success:
            logger.info(f"Test SMS sent successfully via {provider_name}!")
            logger.info(f"Check your phone ({phone_number}) for the test message.")
            return True
        else:
            logger.error(f"Failed to send SMS via {provider_name}")
            return False
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing SMS provider...")
    if test_sms_provider():
        logger.info("SMS provider test completed successfully")
    else:
        logger.error("SMS provider test failed") 