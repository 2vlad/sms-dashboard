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

A service that forwards your Telegram messages to SMS, allowing you to stay connected even when you don't have internet access.

## 🚨 Important Safety Features 🚨

To prevent excessive SMS sending and protect your SMS balance, this application includes several safety features:

1. **Muted Chat Filtering**: By default, messages from muted chats are not forwarded. This prevents unwanted messages from draining your SMS balance.

2. **Rate Limiting**: The application includes a rate limiter that restricts the number of SMS messages that can be sent in a given time period:
   - Global limit: 10 messages per hour by default
   - Per-chat limit: 3 messages per hour from any single chat by default
   - These limits can be adjusted in the Settings page

3. **Configurable Forwarding**: You can configure which types of messages are forwarded:
   - Option to only forward messages from non-muted chats
   - Option to include or exclude media messages
   - Option to include or exclude your own messages

## Setup

1. Clone this repository
2. Install the required packages: `pip install -r requirements.txt`
3. Create a `.env` file with your Telegram API credentials:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   SMSC_LOGIN=your_smsc_login
   SMSC_PASSWORD=your_smsc_password
   ```
4. Run the web application: `python web_app.py`
5. Open the web interface at http://127.0.0.1:5001
6. Log in with your Telegram account
7. Set your phone number in the Settings page
8. Start the forwarder from the Dashboard

## Usage

1. **Dashboard**: View the status of the forwarder and recent messages
2. **Settings**: Configure the forwarder settings, including:
   - Forwarding options (all chats, non-muted chats, media messages, own messages)
   - Rate limiting settings (maximum messages per hour, per chat)
   - SMS settings (maximum SMS length)
3. **Start/Stop Forwarding**: Use the buttons on the Dashboard to start or stop the forwarder

## Troubleshooting

If you encounter issues with the forwarder:

1. Check the logs in `app.log` and `debug_output.txt`
2. Verify your SMS provider credentials
3. Make sure your Telegram session is valid
4. Check the rate limiting settings if messages are not being forwarded

## Deployment

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) for the Telegram client
- All the SMS providers for their services
