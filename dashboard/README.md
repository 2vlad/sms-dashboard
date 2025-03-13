# SMS Dashboard Frontend

This is the frontend part of the SMS Dashboard application, built with Next.js, Tailwind CSS, and ShadCN UI.

## Features

- Modern UI with ShadCN UI components
- Responsive design for desktop and mobile
- Dashboard overview with key metrics
- Message history and management
- User authentication
- Settings management

## Getting Started

### Prerequisites

- Node.js (v14 or higher)

### Installation

1. Clone the repository
```bash
git clone https://github.com/2vlad/sms-dashboard.git
cd sms-dashboard/dashboard
```

2. Install dependencies
```bash
npm install
```

3. Create a `.env.local` file based on `.env.example`
```bash
cp .env.example .env.local
```

4. Start the development server
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Deployment

This project is configured for deployment on Vercel. The main repository includes a `vercel.json` file that specifies the build configuration.

### Environment Variables

Make sure to set the following environment variables in your Vercel project:

- `NEXT_PUBLIC_API_URL`: The URL of your backend API

## Technologies Used

- [Next.js](https://nextjs.org/) - React framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [ShadCN UI](https://ui.shadcn.com/) - UI component library
- [Lucide React](https://lucide.dev/) - Icon library
- Axios for API requests
- Context API for state management
