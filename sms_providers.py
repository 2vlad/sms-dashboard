#!/usr/bin/env python3
"""
SMS Providers Module
This module provides a unified interface for different SMS providers.
"""

import os
import logging
import requests
from abc import ABC, abstractmethod
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

# Define dummy classes for other providers to avoid import errors
class TwilioProvider(SMSProvider):
    """Dummy Twilio SMS provider implementation."""
    
    def __init__(self):
        logger.error("Twilio provider is not available in this deployment")
        raise ValueError("Twilio provider is not available in this deployment")
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using Twilio."""
        raise NotImplementedError("Twilio provider is not available in this deployment")
    
    def verify_credentials(self):
        """Verify Twilio credentials."""
        raise NotImplementedError("Twilio provider is not available in this deployment")

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
    """Dummy MessageBird SMS provider implementation."""
    
    def __init__(self):
        logger.error("MessageBird provider is not available in this deployment")
        raise ValueError("MessageBird provider is not available in this deployment")
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using MessageBird."""
        raise NotImplementedError("MessageBird provider is not available in this deployment")
    
    def verify_credentials(self):
        """Verify MessageBird credentials."""
        raise NotImplementedError("MessageBird provider is not available in this deployment")

class VonageProvider(SMSProvider):
    """Dummy Vonage SMS provider implementation."""
    
    def __init__(self):
        logger.error("Vonage provider is not available in this deployment")
        raise ValueError("Vonage provider is not available in this deployment")
    
    def send_sms(self, message_text, to_number):
        """Send an SMS using Vonage."""
        raise NotImplementedError("Vonage provider is not available in this deployment")
    
    def verify_credentials(self):
        """Verify Vonage credentials."""
        raise NotImplementedError("Vonage provider is not available in this deployment")

def get_sms_provider(provider_name=None):
    """
    Get an instance of the specified SMS provider.
    
    Args:
        provider_name (str, optional): The name of the SMS provider to use.
            If not specified, the SMS_PROVIDER environment variable is used.
            If that is not set, SMSC is used as the default.
    
    Returns:
        SMSProvider: An instance of the specified SMS provider.
    
    Raises:
        ValueError: If the specified provider is not supported or if the required
            environment variables for the provider are not set.
    """
    if not provider_name:
        provider_name = os.getenv('SMS_PROVIDER', 'smsc').lower()
    
    providers = {
        'smsc': SMSCProvider,
        'messagebird': MessageBirdProvider,
        'vonage': VonageProvider,
        'twilio': TwilioProvider
    }
    
    if provider_name not in providers:
        logger.error(f"Unknown SMS provider: {provider_name}. Falling back to SMSC.")
        provider_name = 'smsc'
    
    try:
        logger.info(f"Using SMS provider: {provider_name}")
        return providers[provider_name]()
    except Exception as e:
        logger.error(f"Failed to initialize SMS provider {provider_name}: {e}")
        
        # Only try SMSC as a fallback
        if provider_name != 'smsc':
            try:
                logger.info(f"Falling back to SMSC provider")
                return SMSCProvider()
            except Exception as fallback_e:
                logger.error(f"Failed to initialize fallback SMSC provider: {fallback_e}")
        
        raise ValueError(f"Failed to initialize any SMS provider") 