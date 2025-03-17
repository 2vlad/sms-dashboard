"""
Rate Limiter for SMS Forwarding
This module provides rate limiting functionality to prevent sending too many SMS messages in a short period.
"""

import time
import logging
import os
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Path to store rate limiter state
RATE_LIMITER_STATE_FILE = 'rate_limiter_state.json'

class RateLimiter:
    def __init__(self, max_messages=10, time_window=3600, max_per_chat=3, chat_window=3600, daily_limit=30):
        """
        Initialize the rate limiter.
        
        Args:
            max_messages: Maximum number of messages allowed in the time window
            time_window: Time window in seconds
            max_per_chat: Maximum number of messages allowed per chat in the chat window
            chat_window: Time window for per-chat rate limiting in seconds
            daily_limit: Maximum number of messages allowed per day
        """
        self.max_messages = max_messages
        self.time_window = time_window
        self.max_per_chat = max_per_chat
        self.chat_window = chat_window
        self.daily_limit = daily_limit
        
        # Queue to track message timestamps
        self.message_times = deque()
        
        # Dictionary to track message timestamps per chat
        self.chat_message_times = defaultdict(deque)
        
        # Counter for total messages sent today
        self.daily_counter = 0
        self.daily_reset_time = time.time() + 86400  # 24 hours from now
        
        # Load state from file if it exists
        self.load_state()
    
    def save_state(self):
        """Save the rate limiter state to a file."""
        try:
            state = {
                'max_messages': self.max_messages,
                'time_window': self.time_window,
                'max_per_chat': self.max_per_chat,
                'chat_window': self.chat_window,
                'daily_limit': self.daily_limit,
                'message_times': list(self.message_times),
                'chat_message_times': {str(k): list(v) for k, v in self.chat_message_times.items()},
                'daily_counter': self.daily_counter,
                'daily_reset_time': self.daily_reset_time
            }
            
            with open(RATE_LIMITER_STATE_FILE, 'w') as f:
                json.dump(state, f)
                
            logger.info("Rate limiter state saved to file")
        except Exception as e:
            logger.error(f"Error saving rate limiter state: {e}")
    
    def load_state(self):
        """Load the rate limiter state from a file."""
        if not os.path.exists(RATE_LIMITER_STATE_FILE):
            logger.info("No rate limiter state file found, using default values")
            return
        
        try:
            with open(RATE_LIMITER_STATE_FILE, 'r') as f:
                state = json.load(f)
            
            self.max_messages = state.get('max_messages', self.max_messages)
            self.time_window = state.get('time_window', self.time_window)
            self.max_per_chat = state.get('max_per_chat', self.max_per_chat)
            self.chat_window = state.get('chat_window', self.chat_window)
            self.daily_limit = state.get('daily_limit', self.daily_limit)
            
            self.message_times = deque(state.get('message_times', []))
            
            # Convert string keys back to integers
            self.chat_message_times = defaultdict(deque)
            for k, v in state.get('chat_message_times', {}).items():
                self.chat_message_times[int(k)] = deque(v)
            
            self.daily_counter = state.get('daily_counter', 0)
            self.daily_reset_time = state.get('daily_reset_time', time.time() + 86400)
            
            logger.info("Rate limiter state loaded from file")
            
            # Check if we need to reset the daily counter
            current_time = time.time()
            if current_time > self.daily_reset_time:
                self.daily_counter = 0
                self.daily_reset_time = current_time + 86400  # 24 hours from now
                logger.info("Daily counter reset due to new day")
                self.save_state()
        except Exception as e:
            logger.error(f"Error loading rate limiter state: {e}")
    
    def can_send_message(self, chat_id):
        """
        Check if a message can be sent based on rate limits.
        
        Args:
            chat_id: ID of the chat the message is from
            
        Returns:
            tuple: (can_send, reason)
                can_send: True if the message can be sent, False otherwise
                reason: Reason why the message can't be sent, or None if it can be sent
        """
        current_time = time.time()
        
        # Reset daily counter if needed
        if current_time > self.daily_reset_time:
            self.daily_counter = 0
            self.daily_reset_time = current_time + 86400  # 24 hours from now
            self.save_state()
        
        # Check daily limit
        if self.daily_counter >= self.daily_limit:
            return False, f"Daily limit exceeded: {self.daily_limit} messages per day"
        
        # Remove old timestamps from the global queue
        while self.message_times and current_time - self.message_times[0] > self.time_window:
            self.message_times.popleft()
        
        # Check global rate limit
        if len(self.message_times) >= self.max_messages:
            return False, f"Global rate limit exceeded: {self.max_messages} messages per {self.time_window/3600} hours"
        
        # Remove old timestamps from the chat-specific queue
        if chat_id in self.chat_message_times:
            while (self.chat_message_times[chat_id] and 
                   current_time - self.chat_message_times[chat_id][0] > self.chat_window):
                self.chat_message_times[chat_id].popleft()
        
        # Check chat-specific rate limit
        if len(self.chat_message_times[chat_id]) >= self.max_per_chat:
            return False, f"Chat rate limit exceeded: {self.max_per_chat} messages per {self.chat_window/3600} hours from chat {chat_id}"
        
        # All checks passed
        return True, None
    
    def record_message(self, chat_id):
        """
        Record that a message was sent.
        
        Args:
            chat_id: ID of the chat the message is from
        """
        current_time = time.time()
        
        # Add timestamp to the global queue
        self.message_times.append(current_time)
        
        # Add timestamp to the chat-specific queue
        self.chat_message_times[chat_id].append(current_time)
        
        # Increment daily counter
        self.daily_counter += 1
        
        logger.info(f"Message recorded: {len(self.message_times)}/{self.max_messages} global, " +
                   f"{len(self.chat_message_times[chat_id])}/{self.max_per_chat} for chat {chat_id}, " +
                   f"{self.daily_counter}/{self.daily_limit} total today")
        
        # Save state after recording a message
        self.save_state()
    
    def get_limits_info(self):
        """
        Get information about the current rate limits.
        
        Returns:
            dict: Information about the current rate limits
        """
        current_time = time.time()
        
        # Calculate time until daily reset
        time_until_reset = max(0, self.daily_reset_time - current_time)
        hours, remainder = divmod(time_until_reset, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'global_usage': f"{len(self.message_times)}/{self.max_messages}",
            'daily_usage': f"{self.daily_counter}/{self.daily_limit}",
            'daily_counter': self.daily_counter,
            'daily_limit': self.daily_limit,
            'time_until_reset': f"{int(hours)}h {int(minutes)}m",
            'daily_reset_time': datetime.fromtimestamp(self.daily_reset_time).strftime('%Y-%m-%d %H:%M:%S'),
            'chat_usage': {
                chat_id: f"{len(times)}/{self.max_per_chat}"
                for chat_id, times in self.chat_message_times.items()
            }
        }
        
    def get_daily_usage(self):
        """
        Get the current daily usage count.
        
        Returns:
            int: The number of messages sent today
        """
        return self.daily_counter

# Create a global instance of the rate limiter
# Default: 10 messages per hour globally, max 3 messages per hour from any single chat, 30 messages per day
rate_limiter = RateLimiter(max_messages=10, time_window=3600, max_per_chat=3, chat_window=3600, daily_limit=30) 