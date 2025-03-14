# Configuration for Telegram to SMS Forwarder

# Set to True to forward messages from all chats
FORWARD_ALL_CHATS = True

# Set to True to only forward messages from non-muted chats
# This will override FORWARD_ALL_CHATS if set to True
ONLY_NON_MUTED_CHATS = True

# List of chat usernames or IDs to monitor (if FORWARD_ALL_CHATS is False)
# Example: ['user1', 'user2', 'group1', 123456789]
MONITORED_CHATS = []

# Set to True to include the sender's name in the SMS
INCLUDE_SENDER_NAME = True

# Maximum SMS length (messages longer than this will be truncated)
MAX_SMS_LENGTH = 160

# Set to True to forward media messages (as text notification)
FORWARD_MEDIA = True

# Set to True to forward your own messages
FORWARD_OWN_MESSAGES = False

# Set to True for more detailed logging
DEBUG = False 