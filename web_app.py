#!/usr/bin/env python3
"""
Telegram to SMS Forwarder - Web Interface
This web application provides a simple interface for managing the Telegram to SMS forwarder.
"""

import os
import json
import time
import logging
import sqlite3
import asyncio
import threading
import subprocess
import signal
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from dotenv import load_dotenv
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'FLASK_SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set these environment variables in Railway or in a .env file")
    # Continue anyway to show a proper error page to the user

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

try:
    # Import potentially problematic modules inside try/except
    from telethon import TelegramClient, functions, types, events
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.types import User, Chat, Channel
    from telethon.sessions import StringSession
    import config
    from sms_providers import get_sms_provider
    from flask_session import Session  # Import Flask-Session
    from rate_limiter import rate_limiter
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}", exc_info=True)
    # Continue anyway to show a proper error page to the user

# Create a directory for Telegram sessions
TELEGRAM_SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_sessions')
os.makedirs(TELEGRAM_SESSIONS_DIR, exist_ok=True)
WEB_LOGIN_SESSION_PATH = os.path.join(TELEGRAM_SESSIONS_DIR, 'web_login_session')

# Flask app configuration
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a-fixed-secret-key-for-development-only')

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_sessions')
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True  # Sign the session cookie
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Keep sessions for 30 days
app.config['DATABASE'] = 'forwarder.db'

# Create session directory if it doesn't exist
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize Flask-Session
try:
    Session(app)
except Exception as e:
    logger.error(f"Error initializing Flask-Session: {str(e)}", exc_info=True)

# Make sessions permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True

# Initialize database
def init_db():
    """Initialize the SQLite database."""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            phone_number TEXT,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            auth_date INTEGER,
            last_login INTEGER
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            chat_name TEXT,
            sender_name TEXT,
            message_text TEXT,
            timestamp INTEGER,
            delivered BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create service status table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_status (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            status TEXT,
            last_check INTEGER,
            error_message TEXT,
            pid INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create telegram_messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_messages (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            message_id INTEGER,
            chat_id INTEGER,
            chat_name TEXT,
            sender_name TEXT,
            message_text TEXT,
            timestamp INTEGER,
            forwarded BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, message_id, chat_id)
        )
        ''')
        
        # Create summary_cache table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS summary_cache (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            chat_id INTEGER,
            chat_name TEXT,
            summary_text TEXT,
            message_count INTEGER,
            latest_message_id INTEGER,
            latest_timestamp INTEGER,
            created_at INTEGER,
            updated_at INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, chat_id)
        )
        ''')
        
        # Check if the pid column exists in the service_status table
        cursor.execute("PRAGMA table_info(service_status)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'pid' not in column_names:
            logger.info("Adding pid column to service_status table")
            cursor.execute("ALTER TABLE service_status ADD COLUMN pid INTEGER")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)

# Database helper functions
def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_user(telegram_id):
    """Get a user by Telegram ID."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    conn.close()
    return user

def save_user(telegram_id, phone_number, first_name, last_name, username):
    """Save or update a user."""
    conn = get_db_connection()
    user = get_user(telegram_id)
    
    if user:
        conn.execute(
            'UPDATE users SET phone_number = ?, first_name = ?, last_name = ?, username = ?, last_login = ? WHERE telegram_id = ?',
            (phone_number, first_name, last_name, username, int(time.time()), telegram_id)
        )
    else:
        conn.execute(
            'INSERT INTO users (telegram_id, phone_number, first_name, last_name, username, auth_date, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (telegram_id, phone_number, first_name, last_name, username, int(time.time()), int(time.time()))
        )
    
    conn.commit()
    conn.close()

def save_message(user_id, chat_name, sender_name, message_text, delivered):
    """Save a forwarded message to the database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO messages (user_id, chat_name, sender_name, message_text, delivered, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, chat_name, sender_name, message_text, delivered, int(time.time()))
    )
    conn.commit()
    conn.close()

def get_recent_messages(user_id, limit=10):
    """Get recent messages for a user."""
    conn = get_db_connection()
    messages = conn.execute(
        'SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    conn.close()
    
    return [dict(message) for message in messages]

def get_message_stats(user_id):
    """Get message statistics for a user."""
    conn = get_db_connection()
    
    # Calculate timestamps for today, this week, and this month
    now = datetime.now()
    today_start = int(datetime(now.year, now.month, now.day).timestamp())
    
    # Start of the week (Monday)
    week_day = now.weekday()
    week_start = int((now - timedelta(days=week_day)).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    
    # Start of the month
    month_start = int(datetime(now.year, now.month, 1).timestamp())
    
    # Get counts
    today_count = conn.execute(
        'SELECT COUNT(*) FROM messages WHERE user_id = ? AND timestamp >= ?',
        (user_id, today_start)
    ).fetchone()[0]
    
    week_count = conn.execute(
        'SELECT COUNT(*) FROM messages WHERE user_id = ? AND timestamp >= ?',
        (user_id, week_start)
    ).fetchone()[0]
    
    month_count = conn.execute(
        'SELECT COUNT(*) FROM messages WHERE user_id = ? AND timestamp >= ?',
        (user_id, month_start)
    ).fetchone()[0]
    
    conn.close()
    
    return {
        'today': today_count,
        'week': week_count,
        'month': month_count
    }

# Global variable to store the forwarder process
forwarder_process = None
# Global variable to store active Telegram clients
active_clients = {}

def get_display_name(entity):
    """Get a display name for a user, chat, or channel."""
    if entity is None:
        return "Unknown"
    
    if isinstance(entity, User):
        if entity.first_name and entity.last_name:
            return f"{entity.first_name} {entity.last_name}"
        return entity.first_name or entity.username or str(entity.id)
    
    if isinstance(entity, (Chat, Channel)):
        return entity.title or entity.username or str(entity.id)
    
    return str(entity.id)

def get_media_type(event):
    """Get the type of media in a message."""
    if event.photo:
        return "Photo"
    elif event.video:
        return "Video"
    elif event.audio:
        return "Audio"
    elif event.voice:
        return "Voice"
    elif event.document:
        return "Document"
    elif event.sticker:
        return "Sticker"
    elif event.gif:
        return "GIF"
    else:
        return "Media"

async def is_monitored_chat(client, chat_id):
    """Check if a chat should be monitored based on config."""
    # Add debug logging
    logger.info(f"Checking if chat {chat_id} should be monitored")
    
    # First, check if we should only monitor non-muted chats
    if config.ONLY_NON_MUTED_CHATS:
        try:
            # Get the dialog for this chat
            logger.info(f"ONLY_NON_MUTED_CHATS is enabled, checking if chat {chat_id} is muted")
            dialogs = await client.get_dialogs(limit=100)  # Increase limit to find more chats
            found_dialog = False
            
            for d in dialogs:
                if d.entity.id == chat_id:
                    found_dialog = True
                    # Check if the chat is muted
                    if d.dialog.notify_settings.mute_until:
                        logger.info(f"Chat {chat_id} is muted, skipping")
                        return False
                    else:
                        logger.info(f"Chat {chat_id} is not muted, will be monitored")
                    break
            
            if not found_dialog:
                logger.warning(f"Dialog for chat {chat_id} not found in the first 100 dialogs")
                # If we can't find the dialog, default to monitoring it
                # This ensures we don't miss messages due to dialog retrieval limitations
                return True
                
        except Exception as e:
            logger.error(f"Error checking mute status: {e}")
            # If there's an error checking mute status, default to monitoring the chat
            # to ensure we don't miss important messages
            return True
    
    # Then check other monitoring conditions
    if config.FORWARD_ALL_CHATS:
        logger.info(f"FORWARD_ALL_CHATS is enabled, chat {chat_id} will be monitored")
        return True
    
    if not config.MONITORED_CHATS:
        logger.info(f"No monitored chats configured, chat {chat_id} will not be monitored")
        return False
    
    # Check if chat_id is in the monitored chats list
    if chat_id in config.MONITORED_CHATS:
        logger.info(f"Chat {chat_id} is in MONITORED_CHATS, will be monitored")
        return True
    
    # If chat_id is numeric but monitored chats contains usernames
    try:
        entity = await client.get_entity(chat_id)
        if hasattr(entity, 'username') and entity.username in config.MONITORED_CHATS:
            logger.info(f"Chat {chat_id} username is in MONITORED_CHATS, will be monitored")
            return True
    except Exception as e:
        logger.error(f"Error checking entity: {e}")
    
    logger.info(f"Chat {chat_id} will not be monitored")
    return False

async def get_recent_telegram_messages(user_id, limit=5):
    """Get recent messages from Telegram."""
    global active_clients
    
    logger.info(f"Getting recent Telegram messages for user {user_id}, limit requested: {limit}")
    
    # Create a unique session name for this request
    session_id = f"telegram_session_{user_id}_{int(time.time())}"
    
    # Create client using a StringSession instead of SQLite
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # Connect to Telegram
    try:
        await client.connect()
        
        # Check if authorized - if not, use the web_login_session
        if not await client.is_user_authorized():
            logger.info("Using web_login_session for authorization")
            # Load the auth key from the web_login_session
            web_session = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
            await web_session.connect()
            
            if not await web_session.is_user_authorized():
                logger.error("Not authorized. Please log in first.")
                await web_session.disconnect()
                await client.disconnect()
                return []
            
            # Export the session string
            session_string = StringSession.save(web_session.session)
            await web_session.disconnect()
            
            # Reconnect with the session string
            await client.disconnect()
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Failed to transfer session. Please log in again.")
                await client.disconnect()
                return []
        
        try:
            # Get all dialogs (chats) with a reasonable limit to avoid flood wait
            dialogs = await client.get_dialogs(limit=30)
            
            logger.info(f"Found {len(dialogs)} total dialogs/chats")
            
            # Filter out muted chats if configured to do so
            non_muted_chats = []
            for dialog in dialogs:
                if not dialog.dialog.notify_settings.mute_until:
                    non_muted_chats.append(dialog.entity)
                    # Log each non-muted chat for debugging
                    logger.info(f"Non-muted chat: {get_display_name(dialog.entity)} (ID: {dialog.entity.id})")
                    # Limit to 10 chats to avoid flood wait
                    if len(non_muted_chats) >= 10:
                        break
                else:
                    # Log muted chats for debugging
                    logger.info(f"Skipping muted chat: {get_display_name(dialog.entity)} (ID: {dialog.entity.id})")
            
            logger.info(f"Found {len(non_muted_chats)} non-muted chats")
            
            all_messages = []
            
            # Get recent messages from each non-muted chat
            for idx, chat in enumerate(non_muted_chats[:5]):  # Limit to 5 chats to avoid flood wait
                try:
                    chat_name = get_display_name(chat)
                    logger.info(f"Getting messages from chat {idx+1}/{len(non_muted_chats[:5])}: {chat_name}")
                    
                    # Use a smaller limit per chat to avoid flood wait
                    messages = await client.get_messages(chat, limit=5)  # Increase to 5 messages per chat
                    
                    logger.info(f"Retrieved {len(messages)} messages from chat: {chat_name}")
                    
                    # Log each message retrieved for debugging
                    for msg_idx, message in enumerate(messages):
                        if message.message:  # Only include messages with text
                            logger.info(f"  - Message {msg_idx+1}: {message.message[:30]}...")
                        else:
                            logger.info(f"  - Message {msg_idx+1}: <no text content>")
                    
                    for message in messages:
                        if message.message:  # Only include messages with text
                            sender = await message.get_sender()
                            sender_name = get_display_name(sender) if sender else "Unknown"
                            
                            # Handle media messages
                            if message.media:
                                media_type = get_media_type_from_message(message)
                                message_text = f"[{media_type}]"
                                if message.message:
                                    message_text += f" {message.message}"
                            else:
                                message_text = message.message
                            
                            # Add message to the list
                            all_messages.append({
                                'id': message.id,
                                'chat_id': chat.id,
                                'chat_name': chat_name,
                                'sender_name': sender_name,
                                'message_text': message_text,
                                'timestamp': message.date.timestamp(),
                                'forwarded': False  # Default to not forwarded
                            })
                            logger.info(f"  - Added message: {sender_name} in {chat_name}: {message_text[:30]}...")
                except Exception as e:
                    logger.error(f"Error getting messages from chat {get_display_name(chat)}: {e}")
                    # Don't break the loop, continue with other chats
                    continue
                
                # Add a small delay between chat requests to avoid flood wait
                await asyncio.sleep(0.5)
            
            # Sort all messages by timestamp (newest first)
            all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            logger.info(f"Total messages retrieved before limit: {len(all_messages)}")
            
            # Take only the most recent messages
            recent_messages = all_messages[:limit]
            
            logger.info(f"Returning {len(recent_messages)} recent messages after applying limit {limit}")
            if len(recent_messages) < limit:
                logger.warning(f"Returning fewer messages ({len(recent_messages)}) than requested ({limit}). Check if you have enough active chats with recent messages.")
            
            # Log each message being returned
            for idx, msg in enumerate(recent_messages):
                logger.info(f"Return message {idx+1}: {msg['sender_name']} in {msg['chat_name']}: {msg['message_text'][:30]}...")
            
            # Check which messages have been forwarded
            conn = get_db_connection()
            try:
                for message in recent_messages:
                    # Check if this message has been forwarded
                    forwarded = conn.execute(
                        'SELECT COUNT(*) FROM telegram_messages WHERE user_id = ? AND message_id = ? AND chat_id = ?',
                        (user_id, message['id'], message['chat_id'])
                    ).fetchone()[0] > 0
                    
                    message['forwarded'] = forwarded
            finally:
                conn.close()
            
            return recent_messages
        except Exception as e:
            logger.error(f"Error getting recent Telegram messages: {e}")
            return []
        finally:
            await client.disconnect()
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}")
        return []

def get_media_type_from_message(message):
    """Get the type of media in a message."""
    if message.photo:
        return "Photo"
    elif message.video:
        return "Video"
    elif message.audio:
        return "Audio"
    elif message.voice:
        return "Voice"
    elif message.document:
        return "Document"
    elif message.sticker:
        return "Sticker"
    elif message.gif:
        return "GIF"
    else:
        return "Media"

def save_telegram_message(user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded=True):
    """Save a Telegram message to the database."""
    conn = get_db_connection()
    try:
        # Insert new message record
        conn.execute(
            'INSERT INTO telegram_messages (user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, message_id, chat_id, chat_name, sender_name, message_text, int(time.time()), 1 if forwarded else 0)
        )
        
        conn.commit()
        
        # Also save to messages table for consistency
        save_message(user_id, chat_name, sender_name, message_text, True)
    except Exception as e:
        logger.error(f"Error saving Telegram message: {e}")
        conn.rollback()
    finally:
        conn.close()

async def run_forwarder(user_id, phone_number):
    """Run the Telegram to SMS forwarder."""
    global active_clients
    
    # Create client using the web login session
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    # Store the client in the active_clients dictionary
    active_clients[user_id] = client
    
    # Connect to Telegram
    await client.connect()
    
    # Check if authorized
    if not await client.is_user_authorized():
        logger.error("Not authorized. Please log in first.")
        update_service_status(user_id, 'error', 'Not authorized. Please log in first.')
        return
    
    # Initialize SMS provider
    try:
        sms_provider = get_sms_provider()
        logger.info(f"Using SMS provider: {sms_provider.__class__.__name__}")
        
        # Verify SMS provider credentials
        if not sms_provider.verify_credentials():
            logger.error("SMS provider credentials verification failed")
            update_service_status(user_id, 'error', 'SMS provider credentials verification failed')
            return
            
        # Send a test SMS to verify functionality
        test_message = f"Telegram to SMS Forwarder service started. You will now receive messages via SMS."
        logger.info(f"Sending test SMS to {phone_number}...")
        if not sms_provider.send_sms(test_message, phone_number):
            logger.error(f"Failed to send test SMS to {phone_number}")
            update_service_status(user_id, 'error', f"Failed to send test SMS to {phone_number}")
            return
        logger.info(f"Test SMS sent successfully to {phone_number}")
    except ValueError as e:
        logger.error(f"Failed to initialize SMS provider: {e}")
        update_service_status(user_id, 'error', f"Failed to initialize SMS provider: {e}")
        return
    except Exception as e:
        logger.error(f"Error with SMS provider: {e}")
        update_service_status(user_id, 'error', f"Error with SMS provider: {e}")
        return
    
    # Update service status
    update_service_status(user_id, 'running')
    
    # Add debug logging
    logger.info(f"Forwarder started for user {user_id} with phone number {phone_number}")
    logger.info(f"ONLY_NON_MUTED_CHATS: {config.ONLY_NON_MUTED_CHATS}, FORWARD_ALL_CHATS: {config.FORWARD_ALL_CHATS}")
    
    # Register event handler for new messages
    @client.on(events.NewMessage)
    async def handle_new_message(event):
        try:
            # Add debug logging
            logger.info(f"Received new message event: {event.id}")
            
            # Get the chat where the message was sent
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Add debug logging
            logger.info(f"Message from chat: {chat_id} ({get_display_name(chat)})")
            
            # Skip if this chat is not monitored
            monitored = await is_monitored_chat(client, chat_id)
            logger.info(f"Is chat monitored: {monitored}")
            if not monitored:
                logger.debug(f"Skipping message from non-monitored chat: {chat_id}")
                return
            
            # Skip own messages if configured to do so
            if event.out and not config.FORWARD_OWN_MESSAGES:
                logger.debug("Skipping own message")
                return
            
            # Get the sender
            sender = await event.get_sender()
            sender_name = "You" if event.out else get_display_name(sender)
            
            # Get chat name
            chat_name = get_display_name(chat)
            
            # Handle media messages
            if event.media and config.FORWARD_MEDIA:
                media_type = get_media_type(event)
                message_text = f"[{media_type}]"
                if event.message.text:
                    message_text += f" {event.message.text}"
            else:
                # Skip media messages if not configured to forward them
                if event.media and not config.FORWARD_MEDIA:
                    logger.debug("Skipping media message")
                    return
                
                message_text = event.message.text
            
            # Skip empty messages
            if not message_text:
                logger.debug("Skipping empty message")
                return
            
            # Check rate limits
            can_send, reason = rate_limiter.can_send_message(chat_id)
            if not can_send:
                logger.warning(f"Rate limit exceeded: {reason}")
                return
            
            # Format the message for SMS
            timestamp = datetime.now().strftime("%H:%M:%S")
            if config.INCLUDE_SENDER_NAME:
                sms_text = f"[{timestamp}] {chat_name} - {sender_name}: {message_text}"
            else:
                sms_text = f"[{timestamp}] {chat_name}: {message_text}"
            
            # Get the user's phone number
            phone_number = get_user(user_id)['phone_number']
            if not phone_number:
                logger.error(f"No phone number found for user {user_id}")
                return
            
            # Send the SMS
            try:
                # Truncate message if it's too long
                if len(sms_text) > config.MAX_SMS_LENGTH:
                    sms_text = sms_text[:config.MAX_SMS_LENGTH - 3] + "..."
                
                # Send SMS
                logger.info(f"Sending SMS to {phone_number}: {sms_text[:30]}...")
                success = sms_provider.send_sms(sms_text, phone_number)
                
                if success:
                    logger.info(f"SMS sent successfully to {phone_number}")
                    # Record the message in the rate limiter
                    rate_limiter.record_message(chat_id)
                    
                    # Save the message to the database
                    conn = get_db_connection()
                    conn.execute(
                        'INSERT INTO messages (user_id, chat_id, sender_id, message, timestamp) VALUES (?, ?, ?, ?, ?)',
                        (user_id, chat_id, sender.id if sender else None, message_text, int(time.time()))
                    )
                    conn.commit()
                    conn.close()
                else:
                    logger.error(f"Failed to send SMS to {phone_number}")
                    
            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    # Log that we're starting to listen for messages
    logger.info(f"Started listening for messages for user {user_id}")
    
    try:
        # Run the client until disconnected
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error in forwarder: {e}")
        update_service_status(user_id, 'error', str(e))
    finally:
        # Update service status when disconnected
        update_service_status(user_id, 'stopped')
        logger.info(f"Forwarder stopped for user {user_id}")

def start_forwarder_process(user_id, phone_number):
    """Start the forwarder process."""
    global forwarder_process, active_clients
    
    # Add debug logging
    logger.info(f"Starting forwarder process for user {user_id} with phone number {phone_number}")
    
    # First, make sure any existing forwarder is stopped
    try:
        stop_forwarder_process(user_id)
    except Exception as e:
        logger.error(f"Error stopping existing forwarder: {e}")
        # Continue anyway, as we'll try to start a new one
    
    # Start the forwarder using the service script
    try:
        import subprocess
        import sys
        import os
        
        # Path to the forwarder service script
        service_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_forwarder_service.py')
        
        # Start the forwarder service
        result = subprocess.run([sys.executable, service_script, 'start'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Forwarder service started successfully: {result.stdout.strip()}")
            
            # Update service status with current process ID
            # Extract PID from the output
            import re
            pid_match = re.search(r'PID (\d+)', result.stdout)
            if pid_match:
                pid = int(pid_match.group(1))
                logger.info(f"Updating service status with PID {pid}")
                update_service_status(user_id, 'running', pid=pid)
            else:
                logger.info(f"Updating service status without PID")
                update_service_status(user_id, 'running')
            
            logger.info(f"Forwarder started for user {user_id}")
            return True
        else:
            logger.error(f"Failed to start forwarder service: {result.stderr}")
            update_service_status(user_id, 'error', result.stderr)
            return False
    except Exception as e:
        logger.error(f"Failed to start forwarder: {e}")
        update_service_status(user_id, 'error', str(e))
        return False

def stop_forwarder_process(user_id):
    """Stop the forwarder process."""
    global active_clients
    
    # Get the current status
    status = get_service_status(user_id)
    
    if status['status'] != 'running' or not status.get('pid'):
        logger.info(f"No running forwarder found for user {user_id}")
        update_service_status(user_id, 'stopped')
        return True
    
    try:
        # Stop the forwarder using the service script
        import subprocess
        import sys
        import os
        
        # Path to the forwarder service script
        service_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_forwarder_service.py')
        
        # Stop the forwarder service
        result = subprocess.run([sys.executable, service_script, 'stop'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Forwarder service stopped successfully: {result.stdout.strip()}")
            
            # Update service status
            update_service_status(user_id, 'stopped')
            return True
        else:
            logger.error(f"Failed to stop forwarder service: {result.stderr}")
            # Update service status anyway
            update_service_status(user_id, 'unknown')
            return False
    except Exception as e:
        logger.error(f"Failed to stop forwarder: {e}")
        # Update service status anyway
        update_service_status(user_id, 'unknown')
        return False

def update_service_status(user_id, status, error_message=None, pid=None):
    """Update the service status for a user."""
    conn = get_db_connection()
    
    # Check if there's an existing status for this user
    existing = conn.execute(
        'SELECT id FROM service_status WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    if existing:
        # Update existing status
        conn.execute(
            'UPDATE service_status SET status = ?, last_check = ?, error_message = ?, pid = ? WHERE user_id = ?',
            (status, int(time.time()), error_message, pid, user_id)
        )
    else:
        # Insert new status
        conn.execute(
            'INSERT INTO service_status (user_id, status, last_check, error_message, pid) VALUES (?, ?, ?, ?, ?)',
            (user_id, status, int(time.time()), error_message, pid)
        )
    
    conn.commit()
    conn.close()

def get_service_status(user_id):
    """Get the service status for a user."""
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM service_status WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    if service:
        # Convert to dictionary if it's a sqlite3.Row object
        return dict(service)
    else:
        # Return default status if not found
        return {
            'status': 'unknown',
            'last_check': int(time.time()),
            'error_message': None,
            'pid': None
        }

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # For AJAX requests, return a JSON response instead of redirecting
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'redirect': url_for('login')
                }), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to run async code
def run_async(coro):
    """Run an asynchronous coroutine and return its result."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Get the coroutine name if possible
        coro_name = coro.__qualname__ if hasattr(coro, '__qualname__') else str(coro)
        logger.info(f"Running async coroutine: {coro_name}")
        
        # Special handling for get_all_messages_last_6h which needs more time
        if 'get_all_messages_last_6h' in coro_name:
            timeout = 300  # 5 minutes timeout for message retrieval
            logger.info(f"Using extended timeout of {timeout} seconds for message retrieval")
        else:
            timeout = 60  # 1 minute for other operations
        
        # Set a global timeout for the coroutine
        result = loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
        logger.info("Async coroutine completed successfully")
        return result
    except asyncio.TimeoutError:
        logger.error(f"Async operation timed out after {timeout} seconds")
        raise ConnectionError(f"Operation timed out after {timeout} seconds. Please try again.")
    except ConnectionError as e:
        logger.error(f"Connection error in async operation: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in async operation: {str(e)}", exc_info=True)
        
        # Convert certain errors to more user-friendly ConnectionError
        if "connection" in str(e).lower() or "disconnected" in str(e).lower():
            raise ConnectionError(f"Failed to connect: {str(e)}")
        else:
            raise
    finally:
        try:
            loop.close()
        except:
            pass

# Async Telegram client operations
async def send_code_request_async(phone):
    """Send a code request to Telegram asynchronously."""
    # Maximum number of retries
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(1, max_retries + 1):
        client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
        
        try:
            logger.info(f"Attempt {attempt}/{max_retries}: Connecting to Telegram...")
            
            # Set a timeout for connection
            await asyncio.wait_for(client.connect(), timeout=10)
            
            if await client.is_user_authorized():
                logger.info("Already authorized with existing session")
            
            logger.info(f"Sending code request to Telegram for phone: {phone}")
            
            # Add timeout for send_code_request operation
            sent = await asyncio.wait_for(
                client.send_code_request(
                    phone,
                    force_sms=True
                ),
                timeout=15
            )
            
            logger.info(f"Code request sent successfully. Phone code hash: {sent.phone_code_hash}")
            logger.info(f"Code type: {sent.type}")
            
            return sent.phone_code_hash  # Return the phone_code_hash
            
        except asyncio.TimeoutError:
            logger.error(f"Attempt {attempt}/{max_retries}: Timeout connecting to Telegram or sending code")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Double the delay for next retry (exponential backoff)
                retry_delay *= 2
            else:
                logger.error("Maximum retries reached. Failed to connect to Telegram.")
                raise ConnectionError("Failed to connect to Telegram after multiple attempts. Please try again later.")
                
        except ConnectionError as e:
            logger.error(f"Attempt {attempt}/{max_retries}: Connection error: {str(e)}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Double the delay for next retry (exponential backoff)
                retry_delay *= 2
            else:
                logger.error("Maximum retries reached. Failed to connect to Telegram.")
                raise ConnectionError("Failed to connect to Telegram after multiple attempts. Please try again later.")
                
        except Exception as e:
            logger.error(f"Attempt {attempt}/{max_retries}: Error sending code request: {str(e)}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Double the delay for next retry (exponential backoff)
                retry_delay *= 2
            else:
                logger.error("Maximum retries reached. Failed to send code request.")
                raise e
                
        finally:
            try:
                await client.disconnect()
            except:
                pass

async def sign_in_async(phone, code, phone_code_hash, password=None):
    """Sign in to Telegram asynchronously."""
    client = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
    
    try:
        # Set a timeout for connection
        await asyncio.wait_for(client.connect(), timeout=10)
        
        logger.info(f"Attempting to sign in with phone: {phone}, code: {code}, phone_code_hash: {phone_code_hash}")
        
        try:
            # Set a timeout for sign in
            result = await asyncio.wait_for(
                client.sign_in(
                    phone=phone, 
                    code=code, 
                    phone_code_hash=phone_code_hash
                ),
                timeout=15
            )
            logger.info(f"Sign in successful: {result}")
        except asyncio.TimeoutError:
            logger.error("Sign in timed out")
            return None, False
        except SessionPasswordNeededError:
            logger.info("Two-factor authentication required")
            if not password:
                return None, True  # Need 2FA
            
            logger.info("Attempting to sign in with password")
            try:
                # Set a timeout for password sign in
                await asyncio.wait_for(client.sign_in(password=password), timeout=15)
            except asyncio.TimeoutError:
                logger.error("Password sign in timed out")
                return None, False
        
        # Get the user info with timeout
        try:
            me = await asyncio.wait_for(client.get_me(), timeout=10)
            logger.info(f"Got user info: {me.first_name} (ID: {me.id})")
            return me, False
        except asyncio.TimeoutError:
            logger.error("Getting user info timed out")
            return None, False
    except Exception as e:
        logger.error(f"Error signing in: {str(e)}")
        raise e
    finally:
        try:
            await client.disconnect()
        except:
            pass

# Routes
@app.route('/')
def index():
    """Home page."""
    # Check if the user is logged in
    if session.get('user'):
        return redirect(url_for('dashboard'))
    else:
        # Always redirect to login page, even if there are missing environment variables
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        phone = request.form.get('phone')
        
        if not phone:
            flash('Please enter your phone number', 'error')
            return render_template('login.html')
        
        try:
            # Clean up any existing session files only if they're corrupted
            if os.path.exists(f"{WEB_LOGIN_SESSION_PATH}.session") and not os.path.getsize(f"{WEB_LOGIN_SESSION_PATH}.session") > 0:
                os.remove(f"{WEB_LOGIN_SESSION_PATH}.session")
            
            # Send code request asynchronously and get phone_code_hash
            phone_code_hash = run_async(send_code_request_async(phone))
            
            # Store the phone number and phone_code_hash in the session
            session['phone'] = phone
            session['phone_code_hash'] = phone_code_hash
            
            flash('Verification code has been sent to your Telegram app', 'success')
            return redirect(url_for('verify'))
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            flash('Failed to connect to Telegram. Please check your internet connection and try again.', 'error')
            return render_template('login.html')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            # Display a more user-friendly error message
            if "disconnected" in str(e).lower():
                flash('Connection to Telegram was interrupted. Please try again.', 'error')
            elif "flood" in str(e).lower():
                flash('Too many attempts. Please wait a few minutes before trying again.', 'error')
            elif "user auth" in str(e).lower() or "authorization" in str(e).lower():
                flash('Authentication failed. Please make sure your phone number is correct.', 'error')
            else:
                flash(f'Error: {str(e)}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verification page."""
    if 'phone' not in session or 'phone_code_hash' not in session:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        password = request.form.get('password', '')
        
        if not code:
            flash('Please enter the verification code', 'error')
            return render_template('verify.html')
        
        try:
            logger.info(f"Verifying code for phone: {session['phone']}")
            
            # Sign in asynchronously with phone_code_hash
            try:
                me, need_2fa = run_async(sign_in_async(
                    session['phone'], 
                    code, 
                    session['phone_code_hash'],
                    password
                ))
                
                if me is None:
                    if need_2fa:
                        flash('Two-factor authentication is required', 'info')
                        return render_template('verify.html', two_factor=True)
                    else:
                        flash('Verification failed or timed out. Please try again.', 'error')
                        return render_template('verify.html')
                
                # Save the user to the database
                save_user(
                    me.id,
                    session['phone'],
                    me.first_name,
                    me.last_name if hasattr(me, 'last_name') else '',
                    me.username if hasattr(me, 'username') else ''
                )
                
                # Store the user in the session
                session['user'] = {
                    'id': me.id,
                    'phone': session['phone'],
                    'first_name': me.first_name,
                    'last_name': me.last_name if hasattr(me, 'last_name') else '',
                    'username': me.username if hasattr(me, 'username') else ''
                }
                
                # Make the session permanent
                session.permanent = True
                
                # Clean up
                del session['phone']
                del session['phone_code_hash']
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            except asyncio.TimeoutError:
                flash('Verification timed out. Please try again.', 'error')
                return render_template('verify.html')
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
            return render_template('verify.html')
    
    return render_template('verify.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page."""
    # Get the user's Telegram ID
    user_id = session.get('user', {}).get('id')
    
    if not user_id:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Get the user's phone number
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
    
    if not user:
        # Try to get the first user as a fallback
        user = conn.execute('SELECT * FROM users LIMIT 1').fetchone()
        if user:
            # Update the session with the user info
            session['user'] = {
                'id': user['telegram_id'],
                'phone': user['phone_number'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username']
            }
            user_id = user['telegram_id']
        else:
            flash('No user found. Please login again.', 'error')
            return redirect(url_for('login'))
    
    conn.close()
    
    # Get the service status
    service_status = get_service_status(user_id)
    
    # Get recent messages
    messages = []
    try:
        messages = asyncio.run(get_recent_telegram_messages(user_id))
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
    
    # Get message statistics
    stats = get_message_stats(user_id)
    
    # Get the current usage information
    limits_info = rate_limiter.get_limits_info()
    
    return render_template('dashboard.html', 
                          user=user, 
                          service_status=service_status, 
                          messages=messages,
                          stats=stats,
                          limits_info=limits_info,
                          config={
                              'FORWARD_ALL_CHATS': config.FORWARD_ALL_CHATS,
                              'ONLY_NON_MUTED_CHATS': config.ONLY_NON_MUTED_CHATS,
                              'FORWARD_MEDIA': config.FORWARD_MEDIA,
                              'FORWARD_OWN_MESSAGES': config.FORWARD_OWN_MESSAGES,
                              'MAX_SMS_LENGTH': config.MAX_SMS_LENGTH
                          })

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page."""
    # Get the user's Telegram ID
    user_id = session.get('user', {}).get('id')
    
    if request.method == 'POST':
        # Update settings
        try:
            # Get the settings from the form
            forward_all_chats = request.form.get('forward_all_chats') == 'on'
            only_non_muted_chats = request.form.get('only_non_muted_chats') == 'on'
            forward_media = request.form.get('forward_media') == 'on'
            forward_own_messages = request.form.get('forward_own_messages') == 'on'
            max_sms_length = int(request.form.get('max_sms_length', 160))
            
            # Rate limiter settings
            max_messages = int(request.form.get('max_messages', 10))
            time_window = int(request.form.get('time_window', 3600))
            max_per_chat = int(request.form.get('max_per_chat', 3))
            chat_window = int(request.form.get('chat_window', 3600))
            daily_limit = int(request.form.get('daily_limit', 30))
            
            # Get selected chats from form
            selected_chats = []
            for key in request.form:
                if key.startswith('chat_'):
                    chat_id = key.replace('chat_', '')
                    # Try to convert to integer if possible
                    try:
                        chat_id = int(chat_id)
                    except ValueError:
                        pass
                    selected_chats.append(chat_id)
            
            logger.info(f"Selected chats: {selected_chats}")
            
            # Update the config file
            with open('config.py', 'w') as f:
                f.write(f"""# Configuration for Telegram to SMS Forwarder

# Set to True to forward messages from all chats
FORWARD_ALL_CHATS = {str(forward_all_chats)}

# Set to True to only forward messages from non-muted chats
# This will override FORWARD_ALL_CHATS if set to True
ONLY_NON_MUTED_CHATS = {str(only_non_muted_chats)}

# List of chat usernames or IDs to monitor (if FORWARD_ALL_CHATS is False)
# Example: ['user1', 'user2', 'group1', 123456789]
MONITORED_CHATS = {repr(selected_chats)}

# Set to True to include the sender's name in the SMS
INCLUDE_SENDER_NAME = True

# Maximum SMS length (messages longer than this will be truncated)
MAX_SMS_LENGTH = {max_sms_length}

# Set to True to forward media messages (as text notification)
FORWARD_MEDIA = {str(forward_media)}

# Set to True to forward your own messages
FORWARD_OWN_MESSAGES = {str(forward_own_messages)}

# Set to True for more detailed logging
DEBUG = True
""")
            
            # Update the rate limiter
            rate_limiter.max_messages = max_messages
            rate_limiter.time_window = time_window
            rate_limiter.max_per_chat = max_per_chat
            rate_limiter.chat_window = chat_window
            rate_limiter.daily_limit = daily_limit
            
            # Save the rate limiter state
            rate_limiter.save_state()
            
            # Reload the config module
            import importlib
            importlib.reload(config)
            
            flash('Settings updated successfully', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            flash(f'Error updating settings: {e}', 'error')
    
    # Get the current settings
    current_settings = {
        'forward_all_chats': config.FORWARD_ALL_CHATS,
        'only_non_muted_chats': config.ONLY_NON_MUTED_CHATS,
        'forward_media': config.FORWARD_MEDIA,
        'forward_own_messages': config.FORWARD_OWN_MESSAGES,
        'max_sms_length': config.MAX_SMS_LENGTH,
        'max_messages': rate_limiter.max_messages,
        'time_window': rate_limiter.time_window,
        'max_per_chat': rate_limiter.max_per_chat,
        'chat_window': rate_limiter.chat_window,
        'daily_limit': rate_limiter.daily_limit
    }
    
    # Get the current usage information
    limits_info = rate_limiter.get_limits_info()
    
    return render_template('settings.html', 
                          settings=current_settings, 
                          limits_info=limits_info)

@app.route('/check_status')
@login_required
def check_status():
    """Check the service status."""
    user_id = session.get('user', {}).get('id')
    
    if not user_id:
        # Try to get the first user as a fallback
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users LIMIT 1').fetchone()
        conn.close()
        
        if user:
            user_id = user['telegram_id']
            # Update the session with the user info
            session['user'] = {
                'id': user_id,
                'phone': user['phone_number'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username']
            }
        else:
            return jsonify({'status': 'error', 'message': 'No user found. Please login again.'})
    
    try:
        # Check if the SMS provider is working
        sms_provider = get_sms_provider()
        if sms_provider.verify_credentials():
            # Don't update the status here, just return the current status
            status = get_service_status(user_id)
            return jsonify({'status': status['status'], 'message': status.get('error_message')})
        else:
            update_service_status(user_id, 'error', 'SMS provider credentials verification failed')
            return jsonify({'status': 'error', 'message': 'SMS provider credentials verification failed'})
    except Exception as e:
        update_service_status(user_id, 'error', str(e))
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/start_forwarder')
@login_required
def start_forwarder():
    """Start the forwarder service."""
    user_id = session.get('user', {}).get('id')
    phone_number = session.get('user', {}).get('phone')
    
    if not user_id or not phone_number:
        # Try to get the first user as a fallback
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users LIMIT 1').fetchone()
        conn.close()
        
        if user:
            user_id = user['telegram_id']
            phone_number = user['phone_number']
            # Update the session with the user info
            session['user'] = {
                'id': user_id,
                'phone': phone_number,
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username']
            }
            logger.info(f"Using first user from database: {user_id} with phone {phone_number}")
        else:
            logger.error("No user found in database")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'No user found. Please login again.'})
            flash('No user found. Please login again.', 'error')
            return redirect(url_for('login'))
    
    if not phone_number:
        logger.error(f"No phone number found for user {user_id}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Please set your phone number in settings first'})
        flash('Please set your phone number in settings first', 'error')
        return redirect(url_for('settings'))
    
    # Start the forwarder
    logger.info(f"Starting forwarder for user {user_id} with phone {phone_number}")
    success = start_forwarder_process(user_id, phone_number)
    
    if success:
        logger.info(f"Forwarder started successfully for user {user_id}")
        message = 'Forwarder service started successfully'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': message})
        flash(message, 'success')
    else:
        logger.error(f"Failed to start forwarder for user {user_id}")
        message = 'Failed to start forwarder service'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': message})
        flash(message, 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/stop_forwarder')
@login_required
def stop_forwarder():
    """Stop the forwarder service."""
    user_id = session.get('user', {}).get('id')
    
    if not user_id:
        logger.error("No user ID found in session")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'No user found. Please login again.'})
        flash('No user found. Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Stop the forwarder
    logger.info(f"Stopping forwarder for user {user_id}")
    success = stop_forwarder_process(user_id)
    
    if success:
        logger.info(f"Forwarder stopped successfully for user {user_id}")
        message = 'Forwarder service stopped successfully'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': message})
        flash(message, 'success')
    else:
        logger.error(f"Failed to stop forwarder for user {user_id}")
        message = 'Failed to stop forwarder service'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': message})
        flash(message, 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/refresh_telegram_messages')
@login_required
def refresh_telegram_messages():
    """Refresh Telegram messages for the current user."""
    try:
        user_id = session.get('user', {}).get('id')
        
        if not user_id:
            # Try to get the first user as a fallback
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users LIMIT 1').fetchone()
            conn.close()
            
            if user:
                user_id = user['telegram_id']
                # Update the session with the user info
                session['user'] = {
                    'id': user_id,
                    'phone': user['phone_number'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'username': user['username']
                }
            else:
                return jsonify({'success': False, 'error': 'No user found. Please login again.'})
        
        messages = run_async(get_recent_telegram_messages(user_id, 5))
        
        # Format timestamps for display
        for message in messages:
            message['timestamp_formatted'] = format_timestamp(message['timestamp'])
        
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        app.logger.error(f"Error refreshing Telegram messages: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_recent_messages')
@login_required
def download_recent_messages():
    """Download all messages from non-archived chats as a CSV file."""
    try:
        # Get user_id from session
        user_id = session['user']['id']
        
        logger.info(f"Starting download of messages from non-archived chats for user {user_id}")
        
        # Get all messages from non-archived chats
        all_messages = run_async(get_all_messages_last_6h(user_id))
        
        logger.info(f"Retrieved {len(all_messages)} total messages for download")
        
        if not all_messages:
            logger.warning(f"No messages found in non-archived chats for user {user_id}")
            flash('No messages found in non-archived chats. Please check if you have any non-archived chats with messages.', 'info')
            return redirect(url_for('dashboard'))
        
        # Create CSV content
        csv_content = "Timestamp,Date,Time,Chat,Sender,Message\n"
        
        # Process all messages
        message_count = 0
        for message in all_messages:
            try:
                # Convert timestamp to datetime
                message_date = datetime.fromtimestamp(message['timestamp'])
                date_str = message_date.strftime('%Y-%m-%d')
                time_str = message_date.strftime('%H:%M:%S')
                
                # Escape CSV fields
                chat = str(message['chat_name']).replace(',', ' ').replace('\n', ' ')
                sender = str(message['sender_name']).replace(',', ' ').replace('\n', ' ')
                msg_text = str(message['message_text']).replace(',', ' ').replace('\n', ' ')
                
                # Add to CSV
                csv_content += f"{message['timestamp']},{date_str},{time_str},{chat},{sender},{msg_text}\n"
                message_count += 1
                
                # Log every 10th message for debugging
                if message_count % 10 == 0:
                    logger.info(f"Processed {message_count} messages for CSV")
                
            except Exception as e:
                logger.error(f"Error processing message for CSV: {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully processed {message_count} messages for CSV download")
        
        # Create response with CSV file
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"telegram_messages_nonarchived_{current_time}.csv"
        logger.info(f"Creating CSV response with filename: {filename}")
        
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv"
        
        logger.info(f"CSV download response created successfully with {message_count} messages from non-archived chats")
        return response
        
    except Exception as e:
        logger.error(f"Error downloading messages: {e}", exc_info=True)
        flash('Error downloading messages. Please try again.', 'error')
        return redirect(url_for('dashboard'))

async def get_all_messages_last_6h(user_id):
    """Get all messages from non-archived chats only."""
    global active_clients
    
    logger.info(f"Starting message retrieval for user {user_id} (non-archived chats only)")
    
    # Create client using a StringSession instead of SQLite
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # Connect to Telegram
    try:
        logger.info(f"Connecting to Telegram for user {user_id}")
        await client.connect()
        
        # Check if authorized - if not, use the web_login_session
        if not await client.is_user_authorized():
            logger.info("Using web_login_session for authorization")
            # Load the auth key from the web_login_session
            web_session = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
            await web_session.connect()
            
            if not await web_session.is_user_authorized():
                logger.error("Not authorized. Please log in first.")
                await web_session.disconnect()
                await client.disconnect()
                return []
            
            # Export the session string
            logger.info("Exporting session string from web_login_session")
            session_string = StringSession.save(web_session.session)
            await web_session.disconnect()
            
            # Reconnect with the session string
            logger.info("Reconnecting with session string")
            await client.disconnect()
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Failed to transfer session. Please log in again.")
                await client.disconnect()
                return []
        
        try:
            # Get all dialogs (chats)
            logger.info("Getting dialogs (chats)")
            dialogs = await client.get_dialogs(limit=500)  # Get a large number of dialogs to filter
            logger.info(f"Retrieved {len(dialogs)} total dialogs")
            
            # Filter out archived chats
            non_archived_dialogs = []
            archived_count = 0
            
            for dialog in dialogs:
                # Check if the dialog is archived
                if dialog.archived:
                    archived_count += 1
                    logger.info(f"Skipping archived chat: {get_display_name(dialog.entity)}")
                    continue
                
                non_archived_dialogs.append(dialog)
            
            logger.info(f"Filtered out {archived_count} archived chats, processing {len(non_archived_dialogs)} non-archived chats")
            
            all_messages = []
            chat_count = 0
            
            # Get recent messages from each non-archived chat
            for dialog in non_archived_dialogs:
                try:
                    chat_count += 1
                    chat = dialog.entity
                    chat_name = get_display_name(chat)
                    logger.info(f"[{chat_count}/{len(non_archived_dialogs)}] Getting messages from chat: {chat_name}")
                    
                    # Get messages from this chat
                    messages = await client.get_messages(
                        chat, 
                        limit=200  # Increased limit to get more messages
                    )
                    
                    logger.info(f"Retrieved {len(messages)} messages from chat: {chat_name}")
                    
                    message_count = 0
                    for message in messages:
                        if message.message or message.media:  # Include messages with text or media
                            try:
                                message_count += 1
                                sender = await message.get_sender()
                                sender_name = get_display_name(sender) if sender else "Unknown"
                                
                                # Handle media messages
                                if message.media:
                                    media_type = get_media_type_from_message(message)
                                    message_text = f"[{media_type}]"
                                    if message.message:
                                        message_text += f" {message.message}"
                                else:
                                    message_text = message.message
                                
                                # Skip empty messages
                                if not message_text:
                                    continue
                                
                                # Add message to the list
                                all_messages.append({
                                    'id': message.id,
                                    'chat_id': chat.id,
                                    'chat_name': chat_name,
                                    'sender_name': sender_name,
                                    'message_text': message_text,
                                    'timestamp': message.date.timestamp(),
                                    'date_str': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                                    'forwarded': False  # Default to not forwarded
                                })
                                
                                # Log every 10th message for debugging
                                if message_count % 10 == 0:
                                    logger.info(f"Processed {message_count}/{len(messages)} messages from {chat_name}")
                                
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                                continue
                    
                    logger.info(f"Added {message_count} messages from chat: {chat_name}")
                    
                except Exception as e:
                    logger.error(f"Error getting messages from chat {get_display_name(dialog.entity)}: {e}", exc_info=True)
                    # Don't break the loop, continue with other chats
                    continue
                
                # Add a small delay between chat requests to avoid flood wait
                await asyncio.sleep(0.5)
                
                # Break after processing 20 chats to avoid timeouts
                if chat_count >= 20:
                    logger.info(f"Reached limit of 20 chats, stopping retrieval")
                    break
            
            # Sort all messages by timestamp (newest first)
            all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Log all retrieved messages for debugging
            logger.info(f"All retrieved messages ({len(all_messages)}):")
            for i, msg in enumerate(all_messages[:10]):  # Log first 10 messages
                logger.info(f"Message {i+1}: {msg['chat_name']} - {msg['date_str']} - {msg['message_text'][:30]}...")
            
            logger.info(f"Total messages retrieved: {len(all_messages)}")
            return all_messages
        except Exception as e:
            logger.error(f"Error getting all messages: {e}", exc_info=True)
            return []
        finally:
            logger.info("Disconnecting Telegram client")
            await client.disconnect()
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}", exc_info=True)
        return []

@app.route('/forward_message', methods=['POST'])
@login_required
def forward_message():
    """Manually forward a specific message to SMS."""
    try:
        user_id = session['user']['id']
        data = request.json
        
        # Get user's phone number from database
        conn = get_db_connection()
        user = conn.execute('SELECT phone_number FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user or not user['phone_number']:
            return jsonify({'success': False, 'error': 'No phone number configured. Please set your phone number in settings.'})
        
        phone_number = user['phone_number']
        
        # Prepare message text
        message_id = data.get('message_id')
        chat_id = data.get('chat_id')
        chat_name = data.get('chat_name', 'Unknown')
        sender_name = data.get('sender_name', 'Unknown')
        message_text = data.get('message_text', '')
        
        # Format the SMS message
        sms_text = f"From {sender_name} in {chat_name}: {message_text}"
        
        # Initialize SMS provider
        sms_provider = get_sms_provider()
        
        # Send SMS - note the parameter order: message_text, to_number
        success = sms_provider.send_sms(sms_text, phone_number)
        
        if success:
            # Update message status in database
            conn = get_db_connection()
            
            # First, check if the message exists in the database
            existing = conn.execute(
                'SELECT id FROM telegram_messages WHERE user_id = ? AND message_id = ? AND chat_id = ?',
                (user_id, message_id, chat_id)
            ).fetchone()
            
            if existing:
                # Update existing message
                conn.execute(
                    'UPDATE telegram_messages SET forwarded = 1 WHERE user_id = ? AND message_id = ? AND chat_id = ?',
                    (user_id, message_id, chat_id)
                )
            else:
                # Insert new message record
                conn.execute(
                    'INSERT INTO telegram_messages (user_id, message_id, chat_id, chat_name, sender_name, message_text, timestamp, forwarded) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (user_id, message_id, chat_id, chat_name, sender_name, message_text, int(time.time()), 1 if success else 0)
                )
            
            conn.commit()
            
            # Also save to messages table for consistency
            save_message(user_id, chat_name, sender_name, message_text, True)
            
            conn.close()
            
            app.logger.info(f"Message {message_id} manually forwarded to {phone_number}")
            return jsonify({'success': True})
        else:
            app.logger.error(f"Failed to forward message {message_id}")
            return jsonify({'success': False, 'error': 'Failed to send SMS. Please check your SMS provider configuration.'})
            
    except Exception as e:
        app.logger.error(f"Error forwarding message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def get_sms_provider():
    """Initialize and return the configured SMS provider."""
    provider_name = os.environ.get('SMS_PROVIDER', 'smsc').lower()
    
    try:
        if provider_name == 'twilio':
            from sms_providers import TwilioProvider
            return TwilioProvider()
        elif provider_name == 'messagebird':
            from sms_providers import MessageBirdProvider
            return MessageBirdProvider()
        elif provider_name == 'vonage':
            from sms_providers import VonageProvider
            return VonageProvider()
        else:  # Default to SMSC
            from sms_providers import SMSCProvider
            return SMSCProvider()
    except Exception as e:
        logger.error(f"Error initializing SMS provider {provider_name}: {e}")
        # Try to fall back to another provider
        try:
            logger.info("Falling back to SMSC provider")
            from sms_providers import SMSCProvider
            return SMSCProvider()
        except Exception as e:
            logger.error(f"Error initializing fallback SMS provider: {e}")
            raise ValueError(f"Failed to initialize any SMS provider: {e}")

# Custom template filter for timestamp formatting
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert a timestamp to a formatted datetime string."""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    """Format a timestamp to a human-readable date and time."""
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%b %d, %Y %H:%M:%S')
    except (ValueError, TypeError):
        return "Invalid timestamp"

async def get_all_messages_including_archived(user_id):
    """Get all messages from all chats including archived ones."""
    global active_clients
    
    logger.info(f"Starting message retrieval for user {user_id} (including archived chats)")
    
    # Create client using a StringSession instead of SQLite
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # Connect to Telegram
    try:
        logger.info(f"Connecting to Telegram for user {user_id}")
        await client.connect()
        
        # Check if authorized - if not, use the web_login_session
        if not await client.is_user_authorized():
            logger.info("Using web_login_session for authorization")
            # Load the auth key from the web_login_session
            web_session = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
            await web_session.connect()
            
            if not await web_session.is_user_authorized():
                logger.error("Not authorized. Please log in first.")
                await web_session.disconnect()
                await client.disconnect()
                return []
            
            # Export the session string
            logger.info("Exporting session string from web_login_session")
            session_string = StringSession.save(web_session.session)
            await web_session.disconnect()
            
            # Reconnect with the session string
            logger.info("Reconnecting with session string")
            await client.disconnect()
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Failed to transfer session. Please log in again.")
                await client.disconnect()
                return []
        
        try:
            # Get all dialogs (chats)
            logger.info("Getting all dialogs (including archived)")
            dialogs = await client.get_dialogs(limit=500)  # Get a large number of dialogs
            logger.info(f"Retrieved {len(dialogs)} total dialogs")
            
            # Count archived chats
            archived_count = sum(1 for dialog in dialogs if dialog.archived)
            logger.info(f"Found {archived_count} archived chats out of {len(dialogs)} total")
            
            all_messages = []
            chat_count = 0
            
            # Get recent messages from each chat
            for dialog in dialogs:
                try:
                    chat_count += 1
                    chat = dialog.entity
                    chat_name = get_display_name(chat)
                    
                    # Add archived indicator to chat name
                    if dialog.archived:
                        chat_name = f"{chat_name} [ARCHIVED]"
                    
                    logger.info(f"[{chat_count}/{len(dialogs)}] Getting messages from chat: {chat_name}")
                    
                    # Get messages from this chat
                    messages = await client.get_messages(
                        chat, 
                        limit=100  # Use a smaller limit for all chats to avoid timeouts
                    )
                    
                    logger.info(f"Retrieved {len(messages)} messages from chat: {chat_name}")
                    
                    message_count = 0
                    for message in messages:
                        if message.message or message.media:  # Include messages with text or media
                            try:
                                message_count += 1
                                sender = await message.get_sender()
                                sender_name = get_display_name(sender) if sender else "Unknown"
                                
                                # Handle media messages
                                if message.media:
                                    media_type = get_media_type_from_message(message)
                                    message_text = f"[{media_type}]"
                                    if message.message:
                                        message_text += f" {message.message}"
                                else:
                                    message_text = message.message
                                
                                # Skip empty messages
                                if not message_text:
                                    continue
                                
                                # Add message to the list
                                all_messages.append({
                                    'id': message.id,
                                    'chat_id': chat.id,
                                    'chat_name': chat_name,
                                    'sender_name': sender_name,
                                    'message_text': message_text,
                                    'timestamp': message.date.timestamp(),
                                    'date_str': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                                    'forwarded': False,  # Default to not forwarded
                                    'archived': dialog.archived  # Add archived flag
                                })
                                
                                # Log every 10th message for debugging
                                if message_count % 10 == 0:
                                    logger.info(f"Processed {message_count}/{len(messages)} messages from {chat_name}")
                                
                            except Exception as e:
                                logger.error(f"Error processing message: {e}", exc_info=True)
                                continue
                    
                    logger.info(f"Added {message_count} messages from chat: {chat_name}")
                    
                except Exception as e:
                    logger.error(f"Error getting messages from chat {get_display_name(dialog.entity)}: {e}", exc_info=True)
                    # Don't break the loop, continue with other chats
                    continue
                
                # Add a small delay between chat requests to avoid flood wait
                await asyncio.sleep(0.5)
                
                # Break after processing 30 chats to avoid timeouts
                if chat_count >= 30:
                    logger.info(f"Reached limit of 30 chats, stopping retrieval")
                    break
            
            # Sort all messages by timestamp (newest first)
            all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Log all retrieved messages for debugging
            logger.info(f"All retrieved messages ({len(all_messages)}):")
            for i, msg in enumerate(all_messages[:10]):  # Log first 10 messages
                logger.info(f"Message {i+1}: {msg['chat_name']} - {msg['date_str']} - {msg['message_text'][:30]}...")
            
            logger.info(f"Total messages retrieved: {len(all_messages)}")
            return all_messages
        except Exception as e:
            logger.error(f"Error getting all messages: {e}", exc_info=True)
            return []
        finally:
            logger.info("Disconnecting Telegram client")
            await client.disconnect()
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}", exc_info=True)
        return []

@app.route('/download_all_messages')
@login_required
def download_all_messages():
    """Download messages from all chats including archived ones as a CSV file."""
    try:
        # Get user_id from session
        user_id = session['user']['id']
        
        logger.info(f"Starting download of messages from ALL chats (including archived) for user {user_id}")
        
        # Get all messages including from archived chats
        all_messages = run_async(get_all_messages_including_archived(user_id))
        
        logger.info(f"Retrieved {len(all_messages)} total messages for download (including archived chats)")
        
        if not all_messages:
            logger.warning(f"No messages found in any chats for user {user_id}")
            flash('No messages found in any chats. Please try again later.', 'info')
            return redirect(url_for('dashboard'))
        
        # Create CSV content
        csv_content = "Timestamp,Date,Time,Chat,Sender,Message,Archived\n"
        
        # Process all messages
        message_count = 0
        archived_count = 0
        for message in all_messages:
            try:
                # Convert timestamp to datetime
                message_date = datetime.fromtimestamp(message['timestamp'])
                date_str = message_date.strftime('%Y-%m-%d')
                time_str = message_date.strftime('%H:%M:%S')
                
                # Escape CSV fields
                chat = str(message['chat_name']).replace(',', ' ').replace('\n', ' ')
                sender = str(message['sender_name']).replace(',', ' ').replace('\n', ' ')
                msg_text = str(message['message_text']).replace(',', ' ').replace('\n', ' ')
                archived = "Yes" if message.get('archived', False) else "No"
                
                if message.get('archived', False):
                    archived_count += 1
                
                # Add to CSV
                csv_content += f"{message['timestamp']},{date_str},{time_str},{chat},{sender},{msg_text},{archived}\n"
                message_count += 1
                
                # Log every 10th message for debugging
                if message_count % 10 == 0:
                    logger.info(f"Processed {message_count} messages for CSV")
                
            except Exception as e:
                logger.error(f"Error processing message for CSV: {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully processed {message_count} messages for CSV download (including {archived_count} from archived chats)")
        
        # Create response with CSV file
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"telegram_messages_all_{current_time}.csv"
        logger.info(f"Creating CSV response with filename: {filename}")
        
        response = make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv"
        
        logger.info(f"CSV download response created successfully with {message_count} messages from all chats")
        return response
        
    except Exception as e:
        logger.error(f"Error downloading messages: {e}", exc_info=True)
        flash('Error downloading messages. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/update_daily_limit', methods=['POST'])
@login_required
def update_daily_limit():
    """Update the daily message limit."""
    try:
        # Log the incoming request for debugging
        app.logger.info(f"Received request to update daily limit: {request.data}")
        app.logger.info(f"Request headers: {request.headers}")
        app.logger.info(f"Request content type: {request.content_type}")
        app.logger.info(f"Request is JSON: {request.is_json}")
        
        # Check if the request has JSON data
        if not request.is_json:
            app.logger.error(f"Invalid content type: {request.content_type}. Expected application/json")
            return jsonify({'success': False, 'message': 'Invalid content type. Expected application/json'})
        
        # Get the daily limit from the request
        data = request.get_json()
        app.logger.info(f"Parsed JSON data: {data}")
        
        if not data or 'daily_limit' not in data:
            app.logger.error("Invalid request data for daily limit update: missing daily_limit field")
            return jsonify({'success': False, 'message': 'Invalid request data: missing daily_limit field'})
        
        try:
            daily_limit = int(data['daily_limit'])
        except (ValueError, TypeError) as e:
            app.logger.error(f"Invalid daily limit value: {data['daily_limit']} - {str(e)}")
            return jsonify({'success': False, 'message': f'Invalid daily limit value: {data["daily_limit"]} - must be a number'})
        
        if daily_limit < 1:
            app.logger.error(f"Invalid daily limit value: {daily_limit} - must be greater than 0")
            return jsonify({'success': False, 'message': 'Daily limit must be greater than 0'})
        
        # Update the rate limiter
        app.logger.info(f"Updating rate limiter daily limit from {rate_limiter.daily_limit} to {daily_limit}")
        rate_limiter.daily_limit = daily_limit
        
        # Save the rate limiter state
        app.logger.info("Saving rate limiter state")
        rate_limiter.save_state()
        
        # Get current daily usage
        daily_usage = rate_limiter.get_daily_usage()
        app.logger.info(f"Current daily usage: {daily_usage}")
        
        app.logger.info(f"Daily limit updated to {daily_limit}")
        return jsonify({
            'success': True, 
            'message': 'Daily limit updated successfully',
            'daily_limit': daily_limit,
            'daily_counter': daily_usage
        })
    except Exception as e:
        app.logger.error(f"Error updating daily limit: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error updating daily limit: {str(e)}'})

@app.route('/test_endpoint', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify that the server is working correctly."""
    return jsonify({
        'success': True,
        'message': 'Test endpoint is working correctly',
        'timestamp': time.time()
    })

@app.route('/error', methods=['GET'])
def error_page():
    """Error page."""
    # This page will only be shown if directly accessed
    error = request.args.get('error', 'An unknown error occurred.')
    return render_template('error.html', error=error)

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return render_template('error.html', error=str(error))

def get_cached_summary(user_id, chat_id, chat_name=None):
    """Get a cached summary for a chat if it exists and is not outdated."""
    conn = get_db_connection()
    try:
        # Get the cached summary
        cached = conn.execute(
            'SELECT * FROM summary_cache WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        ).fetchone()
        
        chat_info = f"chat {chat_id}" + (f" ({chat_name})" if chat_name else "")
        
        if cached:
            logger.info(f"Found cached summary for {chat_info}")
            return dict(cached)
        else:
            logger.info(f"No cached summary found for {chat_info}")
            return None
    except Exception as e:
        logger.error(f"Error getting cached summary: {str(e)}")
        return None
    finally:
        conn.close()

def save_summary_to_cache(user_id, chat_id, chat_name, summary_text, message_count, latest_message_id, latest_timestamp):
    """Save or update a summary in the cache."""
    conn = get_db_connection()
    try:
        current_time = int(time.time())
        
        # Check if a summary already exists for this chat
        existing = conn.execute(
            'SELECT id FROM summary_cache WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        ).fetchone()
        
        if existing:
            # Update existing summary
            conn.execute(
                '''UPDATE summary_cache 
                SET summary_text = ?, message_count = ?, latest_message_id = ?, 
                latest_timestamp = ?, updated_at = ?, chat_name = ?
                WHERE user_id = ? AND chat_id = ?''',
                (summary_text, message_count, latest_message_id, latest_timestamp, 
                 current_time, chat_name, user_id, chat_id)
            )
            logger.info(f"Updated cached summary for chat {chat_id} ({chat_name})")
        else:
            # Insert new summary
            conn.execute(
                '''INSERT INTO summary_cache 
                (user_id, chat_id, chat_name, summary_text, message_count, 
                latest_message_id, latest_timestamp, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, chat_id, chat_name, summary_text, message_count, 
                 latest_message_id, latest_timestamp, current_time, current_time)
            )
            logger.info(f"Created new cached summary for chat {chat_id} ({chat_name})")
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving summary to cache: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def should_generate_new_summary(user_id, chat_id, chat_name, messages):
    """Check if we should generate a new summary based on new messages."""
    # Guard clauses
    if not messages:
        logger.warning(f"No messages to generate summary for chat {chat_name}")
        return False
        
    # Sort messages by timestamp (newest first)
    sorted_messages = sorted(messages, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    latest_message = sorted_messages[0]
    latest_message_id = latest_message.get('id')
    latest_timestamp = latest_message.get('timestamp')
    
    # Get cached summary
    cached = get_cached_summary(user_id, chat_id)
    
    # If there's no cached summary, we should generate a new one
    if not cached:
        logger.info(f"No cached summary exists for chat {chat_id} ({chat_name}), generating new one")
        return True
    
    # Safety check - if cached doesn't have the expected fields, generate a new summary
    if 'latest_message_id' not in cached or 'latest_timestamp' not in cached or 'message_count' not in cached:
        logger.warning(f"Cached summary for chat {chat_id} ({chat_name}) is missing fields, generating new one")
        return True
    
    # If the latest message is newer than our cached summary, generate a new one
    if latest_message_id != cached['latest_message_id'] or latest_timestamp > cached['latest_timestamp']:
        logger.info(f"New messages in chat {chat_id} ({chat_name}), generating new summary")
        return True
    
    # If the message count has changed significantly, generate a new summary
    if abs(len(messages) - cached['message_count']) >= 2:  # If 2+ new messages
        logger.info(f"Message count changed for chat {chat_id} ({chat_name}), generating new summary")
        return True
        
    logger.info(f"Using cached summary for chat {chat_id} ({chat_name})")
    return False

async def summarize_messages_with_anthropic(messages):
    """Summarize a list of messages using Anthropic API into a single sentence."""
    try:
        # Get API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in environment variables")
            return None
            
        # Prepare the messages for the API
        message_text = "\n".join([f"{message.get('sender_name', 'Unknown')}: {message.get('message_text', '')}" 
                                  for message in messages if message.get('message_text')])
        
        if not message_text:
            logger.warning("No message text found to summarize")
            return None
            
        logger.info(f"Summarizing {len(messages)} messages")
        
        # Make the API request to Anthropic
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": f"Summarize the following conversation into a single concise sentence that captures the main point or latest topic. Do not start with phrases like 'The user is' or 'The main point of the conversation is'. Simply state the key information directly and concisely:\n\n{message_text}"
                }
            ]
        }
        
        try:
            logger.info("Sending request to Anthropic API")
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10  # Add a timeout to avoid hanging
            )
            
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return None
                
            # Parse the response
            response_data = response.json()
            if not response_data.get('content'):
                logger.error(f"Unexpected Anthropic API response format: {response_data}")
                return None
                
            summary = response_data.get('content', [{}])[0].get('text', '')
            
            if not summary:
                logger.error("Anthropic API returned empty summary")
                return None
                
            # Log and return
            logger.info(f"Generated summary: {summary[:50]}...")
            return summary
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Anthropic API: {str(e)}")
            return None
        
    except Exception as e:
        logger.error(f"Error summarizing messages with Anthropic: {str(e)}")
        return None

async def process_telegram_messages_for_summary(raw_messages, limit=10, user_id=None):
    """
    Process raw telegram messages for the summary view.
    Groups messages by chat and applies special formatting for channels with multiple messages.
    
    Args:
        raw_messages: List of raw Telegram messages
        limit: Maximum number of summaries to return
        user_id: The user's Telegram ID for caching summaries
    
    Returns:
        List of summaries, either one per chat or combined for chats with multiple messages
    """
    if not raw_messages:
        logger.warning("No messages to process for summary")
        return []
    
    logger.info(f"Processing {len(raw_messages)} raw messages for summary")
    
    # Group messages by chat_name
    chat_messages = {}
    for message in raw_messages:
        chat_name = message.get('chat_name', 'Unknown')
        if chat_name not in chat_messages:
            chat_messages[chat_name] = []
        chat_messages[chat_name].append(message)
    
    # Sort messages in each chat by timestamp (newest first)
    for chat_name in chat_messages:
        chat_messages[chat_name].sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    summary_entries = []
    
    for chat_name, messages in chat_messages.items():
        # If more than one message in this chat and we have a user_id, consider summarizing
        if len(messages) > 1 and user_id:
            # Extract chat_id from the first message
            chat_id = messages[0].get('chat_id')
            
            # Skip if no chat_id is present
            if not chat_id:
                logger.warning(f"No chat_id found for {chat_name}, skipping summarization")
                message_text = messages[0].get('message_text', 'No message content')
                is_ai_summary = False
                is_cached = False
                continue
            
            # Get latest message details for caching checks
            latest_message = max(messages, key=lambda x: x.get('timestamp', 0))
            latest_message_id = latest_message.get('id')
            latest_timestamp = latest_message.get('timestamp')
            
            # Check if we should generate a new summary
            cached_summary = get_cached_summary(user_id, chat_id)
            try:
                should_generate = should_generate_new_summary(user_id, chat_id, chat_name, messages)
            except Exception as e:
                logger.error(f"Error checking if summary should be generated: {str(e)}")
                should_generate = True  # Default to generating a new summary if there's an error
            
            # Default values
            is_ai_summary = False
            is_cached = False
            
            if should_generate:
                logger.info(f"Generating new summary for chat {chat_name} (user_id: {user_id}, chat_id: {chat_id})")
                # Use up to 5 recent messages for summarization
                messages_to_summarize = messages[:5]
                # Generate a summary for multiple messages
                try:
                    ai_summary = await summarize_messages_with_anthropic(messages_to_summarize)
                    
                    if ai_summary:
                        logger.info(f"Successfully generated AI summary for {chat_name}")
                        message_text = ai_summary
                        is_ai_summary = True
                        
                        # Store in cache
                        save_summary_to_cache(
                            user_id=user_id,
                            chat_id=chat_id,
                            chat_name=chat_name,
                            summary_text=ai_summary,
                            message_count=len(messages),
                            latest_message_id=latest_message_id,
                            latest_timestamp=latest_timestamp
                        )
                    else:
                        # Fallback to the latest message text if summarization fails
                        logger.warning(f"AI summarization failed for {chat_name}, using latest message text")
                        message_text = messages[0].get('message_text', 'No message content')
                except Exception as e:
                    logger.error(f"Error generating summary for {chat_name}: {str(e)}")
                    message_text = messages[0].get('message_text', 'No message content')
            else:
                # Use cached summary
                if cached_summary:
                    logger.info(f"Using cached summary for chat {chat_name}")
                    message_text = cached_summary['summary_text']
                    is_ai_summary = True
                    is_cached = True
                else:
                    # Fallback to the latest message text if no cached summary
                    logger.info(f"No cached summary for {chat_name}, using latest message text")
                    message_text = messages[0].get('message_text', 'No message content')
        else:
            # For single messages, just use the text directly
            message_text = messages[0].get('message_text', 'No message content')
            is_ai_summary = False
            is_cached = False
        
        # Create a summary entry for this chat
        summary_entry = {
            'chat_name': chat_name,
            'message_text': message_text,
            'timestamp': messages[0].get('timestamp', 0),  # Use the timestamp of the most recent message
            'is_ai_summary': is_ai_summary,
            'is_cached': is_cached
        }
        
        logger.info(f"Created summary entry for {chat_name}: AI={is_ai_summary}, Cached={is_cached}")
        summary_entries.append(summary_entry)
    
    # Sort all summary entries by timestamp (newest first)
    summary_entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    # Return only the limited number of entries
    return summary_entries[:limit]

@app.route('/summary')
@login_required
def summary():
    """Summary page showing recent message summaries."""
    # Get the user's Telegram ID
    user_id = session.get('user', {}).get('id')
    
    if not user_id:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    # Get recent messages from Telegram
    try:
        raw_messages = asyncio.run(get_recent_telegram_messages(user_id, 30))  # Get more messages to group by chat
        messages = asyncio.run(process_telegram_messages_for_summary(raw_messages, 10, user_id))
    except Exception as e:
        logger.error(f"Error getting recent messages for summary: {e}")
        messages = []
    
    # Render the summary template
    return render_template('summary.html', messages=messages)

@app.route('/refresh_summary')
@login_required
def refresh_summary():
    """API endpoint to refresh summary data."""
    try:
        user_id = session.get('user', {}).get('id')
        logger.info(f"Refresh summary request received for user_id: {user_id}")
        
        if not user_id:
            # Try to get the first user as a fallback
            logger.warning("No user ID in session, trying to get first user from database")
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users LIMIT 1').fetchone()
            conn.close()
            
            if user:
                user_id = user['telegram_id']
                logger.info(f"Using first user from database: {user_id}")
                # Update the session with the user info
                session['user'] = {
                    'id': user_id,
                    'phone': user['phone_number'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'username': user['username']
                }
            else:
                logger.error("No user found in database for fallback")
                return jsonify({'success': False, 'error': 'No user found. Please login again.'})
        
        logger.info(f"Getting recent Telegram messages for summary, user_id: {user_id}")
        raw_messages = run_async(get_recent_telegram_messages(user_id, 30))
        logger.info(f"Retrieved {len(raw_messages)} raw messages from Telegram")
        
        logger.info(f"Processing messages for summary display")
        messages = run_async(process_telegram_messages_for_summary(raw_messages, 10, user_id))
        logger.info(f"Processed {len(messages)} messages for summary display")
        
        # Log message details for debugging
        for idx, msg in enumerate(messages):
            logger.info(f"Summary message {idx+1}: {msg.get('chat_name')} - {msg.get('message_text', '')[:30]}...")
        
        logger.info(f"Returning {len(messages)} summary messages to client")
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        logger.error(f"Error refreshing summary data: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

async def get_available_chats(user_id):
    """Get non-archived chats for a user, sorted by most recent activity.
    
    Args:
        user_id: The user's Telegram ID
        
    Returns:
        Dictionary of chats with chat_id as key and dict with name, muted status, and last_activity as value
    """
    logger.info(f"Getting available chats for user {user_id}")
    
    # Create a unique session name for this request
    session_id = f"telegram_session_{user_id}_{int(time.time())}"
    
    # Create client using a StringSession instead of SQLite
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # Connect to Telegram
    try:
        await client.connect()
        
        # Check if authorized - if not, use the web_login_session
        if not await client.is_user_authorized():
            logger.info("Using web_login_session for authorization")
            # Load the auth key from the web_login_session
            web_session = TelegramClient(WEB_LOGIN_SESSION_PATH, API_ID, API_HASH)
            await web_session.connect()
            
            if not await web_session.is_user_authorized():
                logger.error("Not authorized. Please log in first.")
                await web_session.disconnect()
                await client.disconnect()
                return {}
            
            # Export the session string
            session_string = StringSession.save(web_session.session)
            await web_session.disconnect()
            
            # Reconnect with the session string
            await client.disconnect()
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Failed to transfer session. Please log in again.")
                await client.disconnect()
                return {}
        
        try:
            # Get only unarchived dialogs with a larger limit to show more chats
            dialogs = await client.get_dialogs(limit=100, archived=False)
            
            logger.info(f"Found {len(dialogs)} non-archived dialogs/chats")
            
            # Create a dictionary of chat information including mute status and last activity
            chats_dict = {}
            
            for dialog in dialogs:
                chat_id = dialog.entity.id
                chat_name = get_display_name(dialog.entity)
                is_muted = bool(dialog.dialog.notify_settings.mute_until)
                last_activity = dialog.date.timestamp() if dialog.date else 0
                
                # Skip Telegram service chat (unless we want to include it)
                if chat_id == 777000 and chat_name == "Telegram":
                    continue
                    
                # Include all chat types, even one-way channels
                # Add indicator for channel type
                is_channel = dialog.is_channel and not dialog.is_group
                
                # Get the most recent message preview only for visible dialogs
                preview_text = ""
                try:
                    if hasattr(dialog, 'message') and dialog.message and dialog.message.message:
                        # Use the already loaded message to avoid additional API calls
                        preview_text = dialog.message.message[:30] + "..." if len(dialog.message.message) > 30 else dialog.message.message
                except Exception as e:
                    logger.error(f"Error getting preview text for chat {chat_name}: {e}")
                
                chats_dict[chat_id] = {
                    'name': chat_name,
                    'is_muted': is_muted,
                    'is_selected': str(chat_id) in config.MONITORED_CHATS or chat_id in config.MONITORED_CHATS,
                    'last_activity': last_activity,
                    'preview_text': preview_text,
                    'is_channel': is_channel
                }
                
                logger.info(f"Chat: {chat_name} (ID: {chat_id}), Muted: {is_muted}, Last activity: {last_activity}")
            
            logger.info(f"Returning {len(chats_dict)} chats")
            return chats_dict
            
        except Exception as e:
            logger.error(f"Error getting dialogs: {e}")
            return {}
            
    except Exception as e:
        logger.error(f"Error connecting to Telegram: {e}")
        return {}
    finally:
        # Disconnect the client
        await client.disconnect()

@app.route('/chat_selection', methods=['GET', 'POST'])
@login_required
def chat_selection():
    """Chat selection page."""
    # Get the user's Telegram ID
    user_id = session.get('user', {}).get('id')
    
    if request.method == 'POST':
        # Handle form submission
        try:
            # Get selected chats from form
            selected_chats = []
            for key in request.form:
                if key.startswith('chat_'):
                    chat_id = key.replace('chat_', '')
                    # Try to convert to integer if possible
                    try:
                        chat_id = int(chat_id)
                    except ValueError:
                        pass
                    selected_chats.append(chat_id)
            
            logger.info(f"Selected chats: {selected_chats}")
            
            # Update the MONITORED_CHATS in config.py
            config_content = ""
            with open('config.py', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('MONITORED_CHATS ='):
                        line = f"MONITORED_CHATS = {repr(selected_chats)}\n"
                    config_content += line
            
            with open('config.py', 'w') as f:
                f.write(config_content)
            
            # Reload the config module
            import importlib
            importlib.reload(config)
            
            flash('Chat selection updated successfully', 'success')
            return redirect(url_for('chat_selection'))
        except Exception as e:
            logger.error(f"Error updating chat selection: {e}")
            flash(f'Error updating chat selection: {e}', 'error')
    
    # Get available chats
    available_chats = run_async(get_available_chats(user_id))
    
    # Sort chats by last activity (most recent first)
    sorted_chats = {}
    if available_chats:
        # Convert to list of (chat_id, chat_info) tuples, sort by last_activity, and convert back to dict
        sorted_chats_list = sorted(
            available_chats.items(), 
            key=lambda x: x[1]['last_activity'], 
            reverse=True
        )
        sorted_chats = dict(sorted_chats_list)
    
    return render_template('chat_selection.html', available_chats=sorted_chats)

if __name__ == '__main__':
    # Initialize the database directly before running the app
    init_db()
    
    import argparse
    parser = argparse.ArgumentParser(description='Telegram to SMS Forwarder Web App')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Determine if we're in a production environment
    is_production = os.getenv('RAILWAY_ENVIRONMENT') == 'production' or os.getenv('PRODUCTION') == 'true'
    
    # In production, always use 0.0.0.0 as host and disable debug
    if is_production:
        app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
    else:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True) 