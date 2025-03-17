# Telegram to SMS Forwarder

This service forwards your Telegram messages to SMS using various SMS providers.

## Features

- Forward messages from all chats or only selected ones
- Forward media messages (as text notifications)
- Forward your own messages
- Automatically reconnect if the connection is lost
- Automatically restart if the service crashes
- Send notifications when the service starts or stops

## Requirements

- Python 3.6 or higher
- Telegram API credentials (API ID and API Hash)
- SMS provider credentials (SMSC, Twilio, MessageBird, or Vonage)

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your credentials:
   ```
   # Telegram API credentials
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   
   # Your phone number to receive SMS
   YOUR_PHONE_NUMBER=your_phone_number
   
   # SMS Provider Configuration
   SMS_PROVIDER=smsc  # or twilio, messagebird, vonage
   
   # SMSC.ru Configuration
   SMSC_LOGIN=your_login
   SMSC_PASSWORD=your_password
   SMSC_SENDER=SMS  # Optional
   
   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   
   # MessageBird Configuration
   MESSAGEBIRD_API_KEY=your_api_key
   MESSAGEBIRD_ORIGINATOR=SMS  # Optional
   
   # Vonage Configuration
   VONAGE_API_KEY=your_api_key
   VONAGE_API_SECRET=your_api_secret
   VONAGE_FROM_NUMBER=SMS  # Optional
   ```
4. Log in to Telegram using the web app (`web_app.py`)

## Configuration

You can configure the forwarder by editing the `config.py` file:

```python
# Set to True to forward messages from all chats
FORWARD_ALL_CHATS = True

# Set to True to only forward messages from non-muted chats
# This will override FORWARD_ALL_CHATS if set to True
ONLY_NON_MUTED_CHATS = True

# List of chat usernames or IDs to monitor (if FORWARD_ALL_CHATS is False)
# Example: ['user1', 'user2', 'group1', 123456789]
MONITORED_CHATS = ['me']

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
```

## Usage

### Starting the Service

To start the forwarder service:

```
python run_forwarder_service.py start
```

### Stopping the Service

To stop the forwarder service:

```
python run_forwarder_service.py stop
```

### Restarting the Service

To restart the forwarder service:

```
python run_forwarder_service.py restart
```

### Checking the Status

To check if the forwarder service is running:

```
python run_forwarder_service.py status
```

### Running the Service in the Background

To run the forwarder service in the background:

```
nohup python run_forwarder_service.py &
```

### Running the Service at Startup

#### On Linux/macOS

1. Create a systemd service file (Linux) or a launchd plist file (macOS)
2. Configure it to run the `run_forwarder_service.py` script at startup

#### On Windows

1. Create a batch file to run the `run_forwarder_service.py` script
2. Add the batch file to the startup folder

## Logs

The forwarder service creates the following log files:

- `forwarder.log`: Log file for the forwarder script
- `forwarder_service.log`: Log file for the service script
- `forwarder_output.log`: Output of the forwarder process

## Troubleshooting

### The service doesn't start

- Check the log files for errors
- Make sure you have the correct credentials in the `.env` file
- Make sure you're logged in to Telegram using the web app

### The service starts but doesn't forward messages

- Check if the SMS provider is configured correctly
- Check if the Telegram client is authorized
- Check if the chat is monitored (based on the configuration)

### The service stops unexpectedly

- Check the log files for errors
- Make sure the Telegram session is valid
- Make sure the SMS provider is working

## License

This project is licensed under the MIT License - see the LICENSE file for details. 