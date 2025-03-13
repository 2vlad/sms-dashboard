#!/usr/bin/env python3
"""
Test SMS Sending
This script tests the SMS sending functionality using Twilio.
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

# Check if required environment variables are set
required_vars = [
    ('TWILIO_ACCOUNT_SID', TWILIO_ACCOUNT_SID),
    ('TWILIO_AUTH_TOKEN', TWILIO_AUTH_TOKEN),
    ('TWILIO_PHONE_NUMBER', TWILIO_PHONE_NUMBER),
    ('YOUR_PHONE_NUMBER', YOUR_PHONE_NUMBER)
]

missing_vars = [name for name, value in required_vars if not value]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please create a .env file with these variables or set them in your environment.")
    exit(1)

def send_test_sms():
    """Send a test SMS using Twilio."""
    try:
        # Initialize Twilio client
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send the test message
        message = twilio_client.messages.create(
            body="This is a test message from your Telegram to SMS Forwarder.",
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_PHONE_NUMBER
        )
        
        logger.info(f"Test SMS sent successfully! Message SID: {message.sid}")
        logger.info(f"Check your phone ({YOUR_PHONE_NUMBER}) for the test message.")
        
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing SMS sending functionality...")
    success = send_test_sms()
    
    if success:
        logger.info("SMS test completed successfully!")
    else:
        logger.error("SMS test failed. Please check your Twilio credentials and try again.")
        exit(1) 