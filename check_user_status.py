#!/usr/bin/env python3
"""
Check User Status
This script checks the user's session status in the database.
"""

import os
import sqlite3
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database path
DATABASE_PATH = 'forwarder.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_user_status():
    """Check the user's session status in the database."""
    logger.info("Checking user status in the database...")
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # Check users table
        users = conn.execute('SELECT * FROM users').fetchall()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"Found {len(users)} users in the database:")
        for user in users:
            print(f"User ID: {user['id']}")
            print(f"Telegram ID: {user['telegram_id']}")
            print(f"Phone Number: {user['phone_number']}")
            print(f"First Name: {user['first_name']}")
            print(f"Last Name: {user['last_name']}")
            print(f"Username: {user['username']}")
            print(f"Auth Date: {user['auth_date']}")
            print(f"Last Login: {user['last_login']}")
            print("---")
        
        # Check service status
        service_status = conn.execute('SELECT * FROM service_status').fetchall()
        
        if not service_status:
            print("No service status found in the database.")
        else:
            print(f"Found {len(service_status)} service status entries:")
            for status in service_status:
                print(f"User ID: {status['user_id']}")
                print(f"Status: {status['status']}")
                print(f"Last Check: {status['last_check']}")
                print(f"Error Message: {status['error_message']}")
                print(f"PID: {status['pid']}")
                print("---")
        
        # Check messages
        messages = conn.execute('SELECT COUNT(*) as count FROM messages').fetchone()
        print(f"Found {messages['count']} messages in the database.")
        
        # Check telegram_messages
        telegram_messages = conn.execute('SELECT COUNT(*) as count FROM telegram_messages').fetchone()
        print(f"Found {telegram_messages['count']} telegram messages in the database.")
        
    except Exception as e:
        logger.error(f"Error checking user status: {e}")
        print(f"Error checking user status: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_user_status() 