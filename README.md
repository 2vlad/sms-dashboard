# SMS Dashboard

A full-stack application for managing SMS messages with Telegram integration.

## Live Demo

This dashboard is deployed on Vercel at: [https://sms-dashboard-2vlad.vercel.app](https://sms-dashboard-2vlad.vercel.app)

## GitHub Repository

The code is available on GitHub at: [https://github.com/2vlad/sms-dashboard](https://github.com/2vlad/sms-dashboard)

## Project Structure

- **backend**: Node.js/Express API with MongoDB
- **dashboard**: Next.js frontend application

## Features

- User authentication (register, login, profile management)
- SMS message sending and management
- Message statistics and analytics
- Telegram integration for forwarding messages
- User settings management
- Modern UI with ShadCN UI components
- Responsive design for desktop and mobile
- Dashboard overview with key metrics

## Technologies Used

### Backend
- Node.js
- Express
- TypeScript
- MongoDB with Mongoose
- JWT Authentication
- Passport.js
- Telegraf (Telegram Bot API)
- Twilio (SMS API)

### Frontend
- [Next.js](https://nextjs.org/) - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [ShadCN UI](https://ui.shadcn.com/) - UI component library
- [Lucide React](https://lucide.dev/) - Icon library
- Axios for API requests
- Context API for state management

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- MongoDB
- Telegram Bot Token (for Telegram integration)
- Twilio Account (for SMS functionality)

### Installation

1. Clone the repository
```bash
git clone https://github.com/2vlad/sms-dashboard.git
cd sms-dashboard
```

2. Set up the backend
```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your configuration
npm run dev
```

3. Set up the frontend
```bash
cd ../dashboard
npm install
npm run dev
```

4. Access the application
- Backend API: http://localhost:5000
- Frontend: http://localhost:3000

## Deployment

This project is deployed on Vercel. For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## License

MIT

# Telegram to SMS Forwarder

This application forwards your Telegram messages to SMS, allowing you to receive notifications even when you don't have internet access.

## Features

- Forward messages from all chats or only selected ones
- Forward messages from non-muted chats only
- Include sender name in SMS
- Forward media messages (as text notifications)
- Multiple SMS provider options (SMSC.ru, MessageBird, Vonage, Twilio)
- Customizable message format

## Prerequisites

- Python 3.6 or higher
- A Telegram account
- API credentials from Telegram
- An account with one of the supported SMS providers

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/telegram-to-sms-forwarder.git
   cd telegram-to-sms-forwarder
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Copy the example environment file and edit it with your credentials:
   ```
   cp .env.example .env
   nano .env
   ```

## SMS Provider Options

This application supports multiple SMS providers to give you flexibility and cost-effectiveness. Choose the one that works best for your needs:

### 1. SMSC.ru (Recommended for Russian numbers)

SMSC.ru is a Russian SMS provider with good rates for Russian phone numbers. To use SMSC.ru:

1. Sign up at [https://smsc.ru/](https://smsc.ru/)
2. Get your login and password
3. Add the following to your `.env` file:
   ```
   SMS_PROVIDER=smsc
   SMSC_LOGIN=your_login
   SMSC_PASSWORD=your_password
   SMSC_SENDER=SMS  # Optional: your sender ID
   ```

### 2. MessageBird

MessageBird is a global provider with competitive rates. To use MessageBird:

1. Sign up at [https://www.messagebird.com/](https://www.messagebird.com/)
2. Get your API key
3. Add the following to your `.env` file:
   ```
   SMS_PROVIDER=messagebird
   MESSAGEBIRD_API_KEY=your_api_key
   MESSAGEBIRD_ORIGINATOR=SMS  # Optional: your sender ID or phone number
   ```

### 3. Vonage (formerly Nexmo)

Vonage is a global provider with good coverage. To use Vonage:

1. Sign up at [https://www.vonage.com/](https://www.vonage.com/)
2. Get your API key and secret
3. Add the following to your `.env` file:
   ```
   SMS_PROVIDER=vonage
   VONAGE_API_KEY=your_api_key
   VONAGE_API_SECRET=your_api_secret
   VONAGE_FROM_NUMBER=SMS  # Optional: your sender ID or phone number
   ```

### 4. Twilio

Twilio is a popular global provider but can be expensive for international SMS. To use Twilio:

1. Sign up at [https://www.twilio.com/](https://www.twilio.com/)
2. Get your Account SID, Auth Token, and a Twilio phone number
3. Add the following to your `.env` file:
   ```
   SMS_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

## Verifying SMS Provider

You can verify your SMS provider credentials and send a test message using the verification script:

```
python verify_sms_provider.py
```

To get setup instructions for a specific provider:

```
python verify_sms_provider.py --setup smsc
```

To list all available providers:

```
python verify_sms_provider.py --list
```

To verify a specific provider:

```
python verify_sms_provider.py --provider smsc
```

## Configuration

Edit the `config.py` file to customize the behavior of the forwarder:

- `FORWARD_ALL_CHATS`: Set to `True` to forward messages from all chats
- `ONLY_NON_MUTED_CHATS`: Set to `True` to only forward messages from non-muted chats
- `MONITORED_CHATS`: List of chat usernames or IDs to monitor (if `FORWARD_ALL_CHATS` is `False`)
- `INCLUDE_SENDER_NAME`: Set to `True` to include the sender's name in the SMS
- `MAX_SMS_LENGTH`: Maximum SMS length (messages longer than this will be truncated)
- `FORWARD_MEDIA`: Set to `True` to forward media messages (as text notification)
- `FORWARD_OWN_MESSAGES`: Set to `True` to forward your own messages
- `DEBUG`: Set to `True` for more detailed logging

## Usage

1. First, verify your Telegram account:
   ```
   python verify_account.py
   ```

2. Test the SMS sending functionality:
   ```
   python test_sms.py
   ```

3. Run the forwarder:
   ```
   python run_forwarder.py
   ```

The script will authenticate with Telegram (if not already authenticated) and start forwarding messages to your phone via SMS.

## Running in the Background

To run the forwarder in the background, you can use tools like `screen`, `tmux`, or create a systemd service.

Example using `screen`:
```
screen -S telegram-sms
python run_forwarder.py
```
Press `Ctrl+A` followed by `D` to detach from the screen.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for the Telegram client
- All the SMS providers for their services
