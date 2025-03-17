#!/usr/bin/env python3
"""
Reset Telegram Session
This script resets the Telegram session and clears any corrupted session data.
"""

import os
import logging
import shutil
import sqlite3
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Paths
TELEGRAM_SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_sessions')
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')
DATABASE_PATH = 'forwarder.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def reset_telegram_session():
    """Reset the Telegram session and clear any corrupted session data."""
    logger.info("Resetting Telegram session...")
    
    # Check if the session file exists
    session_file = f"{WEB_LOGIN_SESSION_PATH}.session"
    if os.path.exists(session_file):
        logger.info(f"Removing session file: {session_file}")
        try:
            # Create a backup first
            backup_file = f"{session_file}.bak"
            shutil.copy2(session_file, backup_file)
            logger.info(f"Created backup of session file: {backup_file}")
            
            # Remove the session file
            os.remove(session_file)
            logger.info("Session file removed successfully")
        except Exception as e:
            logger.error(f"Error removing session file: {e}")
    else:
        logger.info("No session file found")
    
    # Reset service status in the database
    try:
        conn = get_db_connection()
        
        # Update all service status entries to 'stopped'
        conn.execute('UPDATE service_status SET status = ?, error_message = ?, pid = NULL', 
                    ('stopped', None))
        conn.commit()
        logger.info("Service status reset to 'stopped' in the database")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error resetting service status: {e}")
    
    logger.info("Telegram session reset complete. Please log in again.")

if __name__ == "__main__":
    reset_telegram_session() 