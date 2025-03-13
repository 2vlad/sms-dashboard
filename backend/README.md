# SMS Dashboard Backend

This is the backend API for the SMS Dashboard application, built with Node.js, Express, TypeScript, and MongoDB.

## Features

- User authentication with JWT
- SMS message management
- Message statistics
- User settings management
- Telegram integration

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
cd sms-dashboard/backend
```

2. Install dependencies
```bash
npm install
```

3. Create a `.env` file based on `.env.example`
```bash
cp .env.example .env
```

4. Start the development server
```bash
npm run dev
```

5. The API will be available at [http://localhost:5000](http://localhost:5000)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login a user
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Messages
- `GET /api/messages` - Get all messages
- `POST /api/messages` - Send a new message
- `GET /api/messages/:id` - Get a specific message
- `GET /api/messages/stats` - Get message statistics

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings

### Telegram
- `POST /api/telegram/auth` - Start Telegram authentication
- `POST /api/telegram/verify` - Verify Telegram code
- `POST /api/telegram/disconnect` - Disconnect Telegram account

## Deployment

This backend can be deployed to any Node.js hosting service like Heroku, Render, or a VPS.

### Environment Variables

Make sure to set the following environment variables in your deployment:

- `PORT` - The port to run the server on
- `NODE_ENV` - The environment (development, production)
- `MONGODB_URI` - The MongoDB connection string
- `JWT_SECRET` - The secret key for JWT
- `JWT_EXPIRES_IN` - The JWT expiration time
- `TELEGRAM_BOT_TOKEN` - The Telegram bot token
- `TWILIO_ACCOUNT_SID` - The Twilio account SID
- `TWILIO_AUTH_TOKEN` - The Twilio auth token
- `TWILIO_PHONE_NUMBER` - The Twilio phone number
- `CORS_ORIGIN` - The allowed CORS origin

## Technologies Used

- Node.js
- Express
- TypeScript
- MongoDB with Mongoose
- JWT Authentication
- Passport.js
- Telegraf (Telegram Bot API)
- Twilio (SMS API) 