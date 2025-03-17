#!/usr/bin/env python3
"""
Message Summarizer Module
This module provides functionality to summarize messages and filter out sensitive content.
"""

import re
import logging
from collections import defaultdict
import time
import threading
import config  # Import the config module

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MessageSummarizer:
    """
    Class for summarizing messages and filtering out sensitive content.
    
    This class collects messages from non-muted chats over a period of time,
    then summarizes them while filtering out sensitive content related to
    drugs, weapons, gambling, and adult content.
    
    Instead of sending an SMS for each message immediately, this collects
    multiple messages and sends a single summarized SMS after a delay period.
    This helps reduce the number of SMS messages sent while still providing
    important information.
    """
    
    def __init__(self, delay_seconds=300, max_messages=10, max_summary_length=160):
        """
        Initialize the MessageSummarizer.
        
        Args:
            delay_seconds (int): The delay in seconds before summarizing messages.
            max_messages (int): The maximum number of messages to include in a summary.
            max_summary_length (int): The maximum length of the summary in characters.
        """
        self.delay_seconds = delay_seconds
        self.max_messages = max_messages
        self.max_summary_length = max_summary_length
        self.chat_messages = defaultdict(list)
        self.chat_timers = {}
        self.lock = threading.Lock()
        
        # Use sensitive content patterns from config if available
        if hasattr(config, 'SENSITIVE_CONTENT_PATTERNS') and config.SENSITIVE_CONTENT_PATTERNS:
            self.sensitive_patterns = config.SENSITIVE_CONTENT_PATTERNS
            logger.info(f"Using {len(self.sensitive_patterns)} sensitive content patterns from config")
        else:
            # Default sensitive content patterns to filter out
            self.sensitive_patterns = [
                # Drugs related
                r'\b(?:наркотик|героин|кокаин|марихуан|амфетамин|мет|мефедрон|соль|закладк[аи]|дурь)\b',
                # Weapons related
                r'\b(?:оружие|пистолет|автомат|винтовка|патрон|граната|нож|взрывчатк[аи])\b',
                # Gambling related
                r'\b(?:казино|ставк[аи]|букмекер|тотализатор|азартн|игорн|рулетк[аи]|покер|блэкджек)\b',
                # Adult content related
                r'\b(?:секс|порно|эротик|интим|проститут|эскорт|18\+)\b'
            ]
            logger.info("Using default sensitive content patterns")
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
    
    def add_message(self, chat_id, message_text, sender_name):
        """
        Add a message to be summarized later.
        
        Args:
            chat_id: The ID of the chat the message belongs to.
            message_text (str): The text content of the message.
            sender_name (str): The name of the message sender.
        """
        with self.lock:
            # Add message to the queue
            timestamp = time.time()
            self.chat_messages[chat_id].append({
                'text': message_text,
                'sender': sender_name,
                'timestamp': timestamp
            })
            
            # Start or reset the timer for this chat
            self.reset_timer(chat_id)
            
            logger.info(f"Added message to chat {chat_id}, queue size: {len(self.chat_messages[chat_id])}")
    
    def reset_timer(self, chat_id):
        """
        Reset the timer for a chat.
        
        Args:
            chat_id: The ID of the chat to reset the timer for.
        """
        # Cancel existing timer if any
        if chat_id in self.chat_timers and self.chat_timers[chat_id] is not None:
            self.chat_timers[chat_id].cancel()
        
        # Create new timer
        timer = threading.Timer(self.delay_seconds, self.process_chat_messages, args=[chat_id])
        timer.daemon = True
        timer.start()
        self.chat_timers[chat_id] = timer
        
        logger.debug(f"Reset timer for chat {chat_id}, will process in {self.delay_seconds} seconds")
    
    def process_chat_messages(self, chat_id):
        """
        Process and summarize messages for a chat after the delay period.
        
        Args:
            chat_id: The ID of the chat to process messages for.
        
        Returns:
            str: The summarized message, or None if no summary could be generated.
        """
        with self.lock:
            # Get messages for this chat
            messages = self.chat_messages.get(chat_id, [])
            
            # Clear the messages and timer
            self.chat_messages[chat_id] = []
            self.chat_timers[chat_id] = None
            
            if not messages:
                logger.info(f"No messages to process for chat {chat_id}")
                return None
            
            # Take only the most recent messages up to max_messages
            recent_messages = messages[-self.max_messages:] if len(messages) > self.max_messages else messages
            
            # Generate summary
            summary = self.summarize_messages(recent_messages)
            
            logger.info(f"Generated summary for chat {chat_id}: {summary[:50]}...")
            return summary
    
    def summarize_messages(self, messages):
        """
        Summarize a list of messages.
        
        Args:
            messages (list): A list of message dictionaries.
        
        Returns:
            str: The summarized message.
        """
        if not messages:
            return ""
        
        # Group messages by sender
        sender_messages = defaultdict(list)
        for msg in messages:
            sender_messages[msg['sender']].append(msg['text'])
        
        # Create summary parts
        summary_parts = []
        
        # Add sender summaries
        for sender, texts in sender_messages.items():
            # Join all texts from this sender
            combined_text = " ".join(texts)
            
            # Filter out sensitive content
            safe_text = self.filter_sensitive_content(combined_text)
            
            # Truncate if too long
            if len(safe_text) > 50:
                safe_text = safe_text[:47] + "..."
            
            # Add to summary parts if not empty
            if safe_text.strip():
                summary_parts.append(f"{sender}: {safe_text}")
        
        # Join all parts
        summary = " | ".join(summary_parts)
        
        # Ensure the summary is not too long
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length-3] + "..."
        
        return summary
    
    def filter_sensitive_content(self, text):
        """
        Filter out sensitive content from text.
        
        Args:
            text (str): The text to filter.
        
        Returns:
            str: The filtered text.
        """
        # Replace sensitive content with [filtered]
        filtered_text = text
        for pattern in self.compiled_patterns:
            filtered_text = pattern.sub("[filtered]", filtered_text)
        
        return filtered_text
    
    def get_pending_messages_count(self, chat_id):
        """
        Get the number of pending messages for a chat.
        
        Args:
            chat_id: The ID of the chat to check.
        
        Returns:
            int: The number of pending messages.
        """
        with self.lock:
            return len(self.chat_messages.get(chat_id, []))
    
    def force_process_chat(self, chat_id):
        """
        Force process a chat immediately instead of waiting for the timer.
        
        Args:
            chat_id: The ID of the chat to process.
        
        Returns:
            str: The summarized message, or None if no summary could be generated.
        """
        with self.lock:
            # Cancel the timer if it exists
            if chat_id in self.chat_timers and self.chat_timers[chat_id] is not None:
                self.chat_timers[chat_id].cancel()
                self.chat_timers[chat_id] = None
            
            # Process the messages
            return self.process_chat_messages(chat_id)


# Example usage
if __name__ == "__main__":
    # Create a summarizer with a 10-second delay (for testing)
    summarizer = MessageSummarizer(delay_seconds=10)
    
    # Add some test messages
    summarizer.add_message("chat1", "Hello, how are you?", "Alice")
    summarizer.add_message("chat1", "I'm good, thanks for asking!", "Bob")
    summarizer.add_message("chat1", "What are you doing today?", "Alice")
    
    # Add a message with sensitive content
    summarizer.add_message("chat1", "Do you want to play poker tonight?", "Bob")
    
    # Wait for the timer to expire
    print("Waiting for summary...")
    time.sleep(12)
    
    # Add more messages to a different chat
    summarizer.add_message("chat2", "Hey, are you there?", "Charlie")
    summarizer.add_message("chat2", "Yes, I'm here", "Dave")
    
    # Force process the second chat
    summary = summarizer.force_process_chat("chat2")
    print(f"Forced summary: {summary}")
    
    # Wait for all threads to finish
    time.sleep(2) 