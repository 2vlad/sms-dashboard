#!/usr/bin/env python3
"""
SMS Providers Module
This module provides a unified interface for different SMS providers.
"""

import os
import logging
import requests
from abc import ABC, abstractmethod
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

class SMSProvider(ABC):
    """Abstract base class for SMS providers."""
    
    @abstractmethod
    def send_sms(self, message_text, to_number):
        """Send an SMS message."""
        pass
    
    @abstractmethod
    def verify_credentials(self):
        """Verify that the provider credentials are valid."""
        pass

class TwilioProvider(SMSProvider):
    """Twilio SMS provider implementation."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Check if required environment variables are set
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.error("Missing required Twilio environment variables")
            raise ValueError("Missing required Twilio environment variables")
        
        self.client = TwilioClient(self.account_sid, self.auth_token)
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using Twilio."""
        try:
            message = self.client.messages.create(
                body=message_text,
                from_=self.phone_number,
                to=to_number
            )
            logger.info(f"SMS sent successfully via Twilio: {message.sid}")
            return True
        except TwilioRestException as e:
            logger.error(f"Failed to send SMS via Twilio: {e}")
            return False
    
    def verify_credentials(self):
        """Verify Twilio credentials."""
        try:
            # Try to access account info to verify credentials
            account = self.client.api.accounts(self.account_sid).fetch()
            logger.info(f"Twilio credentials verified for account: {account.friendly_name}")
            return True
        except TwilioRestException as e:
            logger.error(f"Twilio credentials verification failed: {e}")
            return False

class SMSCProvider(SMSProvider):
    """SMSC.ru SMS provider implementation."""
    
    def __init__(self):
        self.login = os.getenv('SMSC_LOGIN')
        self.password = os.getenv('SMSC_PASSWORD')
        self.sender = os.getenv('SMSC_SENDER', 'SMS')
        
        # Check if required environment variables are set
        if not all([self.login, self.password]):
            logger.error("Missing required SMSC environment variables")
            raise ValueError("Missing required SMSC environment variables")
        
        # API endpoint
        self.base_url = "https://smsc.ru/sys/send.php"
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using SMSC.ru."""
        params = {
            'login': self.login,
            'psw': self.password,
            'phones': to_number,
            'mes': message_text,
            'sender': self.sender,
            'fmt': 3,  # JSON response format
            'charset': 'utf-8'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                logger.error(f"Failed to send SMS via SMSC: {result['error']}")
                return False
            
            logger.info(f"SMS sent successfully via SMSC: {result.get('id', 'Unknown ID')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS via SMSC: {e}")
            return False
    
    def verify_credentials(self):
        """Verify SMSC credentials."""
        params = {
            'login': self.login,
            'psw': self.password,
            'get_balance': 1,
            'fmt': 3  # JSON response format
        }
        
        try:
            response = requests.get("https://smsc.ru/sys/balance.php", params=params)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                logger.error(f"SMSC credentials verification failed: {result['error']}")
                return False
            
            logger.info(f"SMSC credentials verified. Balance: {result.get('balance', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"SMSC credentials verification failed: {e}")
            return False

class MessageBirdProvider(SMSProvider):
    """MessageBird SMS provider implementation."""
    
    def __init__(self):
        self.api_key = os.getenv('MESSAGEBIRD_API_KEY')
        self.originator = os.getenv('MESSAGEBIRD_ORIGINATOR', 'SMS')
        
        # Check if required environment variables are set
        if not self.api_key:
            logger.error("Missing required MessageBird environment variables")
            raise ValueError("Missing required MessageBird environment variables")
        
        # API endpoint
        self.base_url = "https://rest.messagebird.com/messages"
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using MessageBird."""
        headers = {
            'Authorization': f'AccessKey {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'originator': self.originator,
            'recipients': [to_number],
            'body': message_text
        }
        
        try:
            response = requests.post(self.base_url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"SMS sent successfully via MessageBird: {result.get('id', 'Unknown ID')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS via MessageBird: {e}")
            return False
    
    def verify_credentials(self):
        """Verify MessageBird credentials."""
        headers = {
            'Authorization': f'AccessKey {self.api_key}'
        }
        
        try:
            response = requests.get("https://rest.messagebird.com/balance", headers=headers)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"MessageBird credentials verified. Balance: {result.get('amount', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"MessageBird credentials verification failed: {e}")
            return False

class VonageProvider(SMSProvider):
    """Vonage (formerly Nexmo) SMS provider implementation."""
    
    def __init__(self):
        self.api_key = os.getenv('VONAGE_API_KEY')
        self.api_secret = os.getenv('VONAGE_API_SECRET')
        self.from_number = os.getenv('VONAGE_FROM_NUMBER', 'SMS')
        
        # Check if required environment variables are set
        if not all([self.api_key, self.api_secret]):
            logger.error("Missing required Vonage environment variables")
            raise ValueError("Missing required Vonage environment variables")
        
        # API endpoint
        self.base_url = "https://rest.nexmo.com/sms/json"
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using Vonage."""
        data = {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'from': self.from_number,
            'to': to_number,
            'text': message_text
        }
        
        try:
            response = requests.post(self.base_url, data=data)
            response.raise_for_status()
            result = response.json()
            
            # Check if all messages were sent successfully
            if result['message-count'] == '0':
                logger.error(f"Failed to send SMS via Vonage: No messages sent")
                return False
            
            for message in result['messages']:
                if message['status'] != '0':
                    logger.error(f"Failed to send SMS via Vonage: {message['error-text']}")
                    return False
            
            logger.info(f"SMS sent successfully via Vonage")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS via Vonage: {e}")
            return False
    
    def verify_credentials(self):
        """Verify Vonage credentials."""
        data = {
            'api_key': self.api_key,
            'api_secret': self.api_secret
        }
        
        try:
            response = requests.get("https://rest.nexmo.com/account/get-balance", params=data)
            response.raise_for_status()
            result = response.json()
            
            if 'error-code' in result and result['error-code'] != '0':
                logger.error(f"Vonage credentials verification failed: {result.get('error-text', 'Unknown error')}")
                return False
            
            logger.info(f"Vonage credentials verified. Balance: {result.get('value', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Vonage credentials verification failed: {e}")
            return False

def get_sms_provider(provider_name=None):
    """
    Factory function to get the appropriate SMS provider.
    If provider_name is not specified, it will be read from the SMS_PROVIDER environment variable.
    """
    if not provider_name:
        provider_name = os.getenv('SMS_PROVIDER', 'twilio').lower()
    
    providers = {
        'twilio': TwilioProvider,
        'smsc': SMSCProvider,
        'messagebird': MessageBirdProvider,
        'vonage': VonageProvider
    }
    
    if provider_name not in providers:
        logger.error(f"Unknown SMS provider: {provider_name}. Falling back to Twilio.")
        provider_name = 'twilio'
    
    try:
        return providers[provider_name]()
    except ValueError as e:
        logger.error(f"Failed to initialize {provider_name} provider: {e}")
        
        # Try to fall back to another provider if the requested one fails
        for fallback in ['smsc', 'messagebird', 'vonage', 'twilio']:
            if fallback != provider_name:
                try:
                    logger.info(f"Trying fallback provider: {fallback}")
                    return providers[fallback]()
                except ValueError:
                    continue
        
        raise ValueError("No SMS provider could be initialized. Check your environment variables.") 