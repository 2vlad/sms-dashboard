#!/usr/bin/env python3
"""
Check SMSC Balance
This script checks the SMSC balance and status.
"""

import os
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# SMSC credentials
SMSC_LOGIN = os.getenv('SMSC_LOGIN')
SMSC_PASSWORD = os.getenv('SMSC_PASSWORD')

def check_smsc_balance():
    """Check the SMSC balance and status."""
    logger.info("Checking SMSC balance and status...")
    
    if not SMSC_LOGIN or not SMSC_PASSWORD:
        logger.error("SMSC credentials not found in environment variables")
        return False
    
    try:
        # API endpoint for checking balance
        url = 'https://smsc.ru/sys/balance.php'
        
        # Parameters for the request
        params = {
            'login': SMSC_LOGIN,
            'psw': SMSC_PASSWORD,
            'fmt': 3  # JSON format
        }
        
        # Make the request
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Print the balance information
            print("\n=== SMSC Account Information ===")
            print(f"Balance: {data.get('balance', 'N/A')} RUB")
            print(f"Credit: {data.get('credit', 'N/A')} RUB")
            print(f"Currency: {data.get('currency', 'N/A')}")
            
            # Check if there are any active messages in the queue
            url_status = 'https://smsc.ru/sys/status.php'
            params_status = {
                'login': SMSC_LOGIN,
                'psw': SMSC_PASSWORD,
                'fmt': 3,  # JSON format
                'all': 1    # Get all messages
            }
            
            response_status = requests.get(url_status, params=params_status)
            
            if response_status.status_code == 200:
                status_data = response_status.json()
                
                if isinstance(status_data, list) and len(status_data) > 0:
                    print("\n=== Pending Messages ===")
                    for msg in status_data:
                        print(f"ID: {msg.get('id', 'N/A')}")
                        print(f"Status: {msg.get('status', 'N/A')}")
                        print(f"Phone: {msg.get('phone', 'N/A')}")
                        print(f"Time: {msg.get('time', 'N/A')}")
                        print(f"Cost: {msg.get('cost', 'N/A')} RUB")
                        print("---")
                else:
                    print("\nNo pending messages in the queue.")
            else:
                print(f"\nError checking message status: {response_status.text}")
            
            return True
        else:
            logger.error(f"Error checking SMSC balance: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking SMSC balance: {e}")
        return False

def clear_smsc_queue():
    """Clear any pending messages in the SMSC queue."""
    logger.info("Clearing SMSC queue...")
    
    if not SMSC_LOGIN or not SMSC_PASSWORD:
        logger.error("SMSC credentials not found in environment variables")
        return False
    
    try:
        # First, get all pending messages
        url_status = 'https://smsc.ru/sys/status.php'
        params_status = {
            'login': SMSC_LOGIN,
            'psw': SMSC_PASSWORD,
            'fmt': 3,  # JSON format
            'all': 1    # Get all messages
        }
        
        response_status = requests.get(url_status, params=params_status)
        
        if response_status.status_code == 200:
            status_data = response_status.json()
            
            if isinstance(status_data, list) and len(status_data) > 0:
                print("\n=== Clearing Pending Messages ===")
                
                # API endpoint for canceling messages
                url_cancel = 'https://smsc.ru/sys/send.php'
                
                for msg in status_data:
                    msg_id = msg.get('id')
                    if msg_id:
                        # Parameters for canceling the message
                        params_cancel = {
                            'login': SMSC_LOGIN,
                            'psw': SMSC_PASSWORD,
                            'fmt': 3,  # JSON format
                            'cancel': msg_id
                        }
                        
                        # Make the request
                        response_cancel = requests.get(url_cancel, params=params_cancel)
                        
                        if response_cancel.status_code == 200:
                            print(f"Canceled message with ID: {msg_id}")
                        else:
                            print(f"Error canceling message with ID {msg_id}: {response_cancel.text}")
                
                print("\nAll pending messages have been cleared.")
            else:
                print("\nNo pending messages to clear.")
            
            return True
        else:
            logger.error(f"Error checking message status: {response_status.text}")
            return False
    except Exception as e:
        logger.error(f"Error clearing SMSC queue: {e}")
        return False

if __name__ == "__main__":
    print("1. Check SMSC balance and status")
    print("2. Clear SMSC queue")
    print("3. Both")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == '1':
        check_smsc_balance()
    elif choice == '2':
        clear_smsc_queue()
    elif choice == '3':
        check_smsc_balance()
        clear_smsc_queue()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.") 