#!/usr/bin/env python3
"""
Update Database Schema
This script updates the database schema to add the pid column to the service_status table.
"""

import sqlite3
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = 'forwarder.db'

def update_db_schema():
    """Update the database schema."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if the pid column exists in the service_status table
    cursor.execute("PRAGMA table_info(service_status)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'pid' not in column_names:
        logger.info("Adding pid column to service_status table")
        cursor.execute("ALTER TABLE service_status ADD COLUMN pid INTEGER")
        conn.commit()
        logger.info("pid column added successfully")
    else:
        logger.info("pid column already exists in service_status table")
    
    # Close the connection
    conn.close()
    logger.info("Database schema update completed")

if __name__ == "__main__":
    update_db_schema() 