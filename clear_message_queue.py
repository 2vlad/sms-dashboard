#!/usr/bin/env python3
"""
Clear Message Queue
This script clears any pending messages in the queue and resets the rate limiter.
"""

import os
import sqlite3
import logging
import time
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

def clear_message_queue():
    """Clear any pending messages in the queue."""
    logger.info("Clearing message queue...")
    
    # Connect to the database
    conn = get_db_connection()
    
    try:
        # 1. Reset the rate limiter by deleting the rate_limiter.py file and recreating it
        logger.info("Resetting rate limiter...")
        
        # Import and reset the rate limiter
        try:
            from rate_limiter import rate_limiter
            rate_limiter.message_times.clear()
            rate_limiter.chat_message_times.clear()
            rate_limiter.daily_counter = 0
            rate_limiter.daily_reset_time = time.time() + 86400  # 24 hours from now
            logger.info("Rate limiter reset successfully")
        except ImportError:
            logger.warning("Rate limiter module not found, skipping reset")
        
        # 2. Update all service statuses to 'stopped'
        logger.info("Updating service statuses...")
        conn.execute('UPDATE service_status SET status = ?', ('stopped',))
        logger.info("Service statuses updated")
        
        # 3. Kill any running forwarder processes
        logger.info("Checking for running forwarder processes...")
        services = conn.execute('SELECT * FROM service_status WHERE pid IS NOT NULL').fetchall()
        
        for service in services:
            pid = service['pid']
            if pid:
                logger.info(f"Found process with PID {pid}, attempting to terminate...")
                try:
                    # Try to kill the process
                    import signal
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Process with PID {pid} terminated")
                except ProcessLookupError:
                    logger.info(f"Process with PID {pid} not found, it may have already terminated")
                except Exception as e:
                    logger.error(f"Error terminating process with PID {pid}: {e}")
                
                # Update the service status to remove the PID
                conn.execute('UPDATE service_status SET pid = NULL WHERE pid = ?', (pid,))
        
        # 4. Clear any pending messages in the telegram_messages table
        logger.info("Clearing pending messages...")
        conn.execute('UPDATE telegram_messages SET forwarded = ? WHERE forwarded = ?', (1, 0))
        logger.info("Pending messages cleared")
        
        # Commit all changes
        conn.commit()
        logger.info("All changes committed to database")
        
        logger.info("Message queue cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing message queue: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clear_message_queue()
    print("Message queue cleared successfully. You can now restart the forwarder.") 