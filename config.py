# Configuration for Telegram to SMS Forwarder

# Set to True to forward messages from all chats
# Note: If ONLY_NON_MUTED_CHATS is True, this will only apply to non-muted chats
FORWARD_ALL_CHATS = False

# Set to True to only forward messages from non-muted chats
# This will filter out muted chats even if FORWARD_ALL_CHATS is True
ONLY_NON_MUTED_CHATS = True

# List of chat usernames or IDs to monitor (if FORWARD_ALL_CHATS is False)
# Example: ['user1', 'user2', 'group1', 123456789]
MONITORED_CHATS = [264409467, 1894658755, 128696146, 89118240, 1744645276, 257621, 1012166586, 320320489, 301587810, 151742, 401570492, 348332, 289922440, 6896576313]

# Set to True to include the sender's name in the SMS
INCLUDE_SENDER_NAME = True

# Maximum SMS length (messages longer than this will be truncated)
MAX_SMS_LENGTH = 160

# Set to True to forward media messages (as text notification)
FORWARD_MEDIA = True

# Set to True to forward your own messages
FORWARD_OWN_MESSAGES = True

# Set to True for more detailed logging
DEBUG = True

# Message summarizer configuration
# Set to True to enable message summarization for non-muted chats
# When enabled, messages from non-muted chats will be collected and summarized
# before sending as a single SMS, rather than sending each message immediately
ENABLE_MESSAGE_SUMMARIZATION = True

# Delay in seconds before summarizing messages (default: 5 minutes)
SUMMARIZATION_DELAY = 300

# Maximum number of messages to include in a summary
MAX_SUMMARY_MESSAGES = 10

# List of sensitive content patterns to filter out from summaries
# These are regex patterns that will be replaced with [filtered]
SENSITIVE_CONTENT_PATTERNS = [
    # Drugs related
    r'\b(?:наркотик|героин|кокаин|марихуан|амфетамин|мет|мефедрон|соль|закладк[аи]|дурь)\b',
    # Weapons related
    r'\b(?:оружие|пистолет|автомат|винтовка|патрон|граната|нож|взрывчатк[аи])\b',
    # Gambling related
    r'\b(?:казино|ставк[аи]|букмекер|тотализатор|азартн|игорн|рулетк[аи]|покер|блэкджек)\b',
    # Adult content related
    r'\b(?:секс|порно|эротик|интим|проститут|эскорт|18\+)\b'
]
