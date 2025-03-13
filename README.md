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
