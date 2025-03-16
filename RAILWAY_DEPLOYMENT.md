# Deploying Telegram to SMS Forwarder on Railway.app

Railway.app is a modern cloud platform that makes it easy to deploy your applications. It's similar to Vercel but better suited for Python applications and services that need to run continuously.

## Prerequisites

1. A GitHub account
2. A Railway.app account (you can sign up at [railway.app](https://railway.app) using your GitHub account)

## Deployment Steps

### 1. Push your code to GitHub

1. Create a new repository on GitHub (if you haven't already)
2. Initialize Git in your project folder (if not already done):
   ```bash
   git init
   ```
3. Add all files to Git:
   ```bash
   git add .
   ```
4. Commit the changes:
   ```bash
   git commit -m "Prepare for Railway deployment"
   ```
5. Add your GitHub repository as a remote:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo-name.git
   ```
6. Push the code to GitHub:
   ```bash
   git push -u origin main
   ```

### 2. Deploy to Railway.app

1. Go to [railway.app](https://railway.app) and sign in with your GitHub account
2. Click on "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository from the list
5. Railway will automatically detect your project configuration
6. Click "Deploy"

### 3. Set up Environment Variables

1. In your Railway project dashboard, go to the "Variables" tab
2. Add the following environment variables:
   - `TELEGRAM_API_ID` - Your Telegram API ID
   - `TELEGRAM_API_HASH` - Your Telegram API Hash
   - `SMSC_LOGIN` - Your SMSC login
   - `SMSC_PASSWORD` - Your SMSC password
   - Any other environment variables your application needs

### 4. Set up Multiple Services (Web App and Forwarder)

Railway allows you to run multiple services within a single project:

1. In your project dashboard, go to the "Services" tab
2. You should see your main service running the web app
3. Click "New Service" and select "Deploy from GitHub repo"
4. Choose the same repository
5. In the service settings, change the "Start Command" to `python run_forwarder_service.py`
6. Make sure to add the same environment variables to this service

### 5. Set up Persistent Storage

For your Telegram sessions and database:

1. In your project dashboard, go to the "Volumes" tab
2. Click "New Volume"
3. Name it "data"
4. Mount it at `/app/data`
5. Create another volume named "telegram_sessions" and mount it at `/app/telegram_sessions`
6. Create another volume named "flask_sessions" and mount it at `/app/flask_sessions`
7. Attach these volumes to both your web app and forwarder services

### 6. Custom Domain (Optional)

1. In your Railway project dashboard, go to the "Settings" tab
2. Scroll down to "Domains"
3. Click "Generate Domain" for a railway.app subdomain or "Custom Domain" to use your own domain
4. Follow the instructions to configure DNS settings if using a custom domain

## Continuous Deployment

Railway automatically sets up continuous deployment. Any changes pushed to your main branch will trigger a new deployment.

## Monitoring and Logs

1. In your Railway project dashboard, go to the "Deployments" tab to see deployment history
2. Click on a deployment to view logs
3. You can also view real-time logs by clicking on a service and then the "Logs" tab

## Scaling (if needed)

Railway allows you to scale your application:

1. In your service settings, go to the "Scaling" tab
2. Adjust the memory and CPU allocation as needed

## Troubleshooting

If you encounter any issues:

1. Check the logs for error messages
2. Make sure all environment variables are set correctly
3. Verify that your volumes are mounted correctly
4. Try redeploying the service

## Cost Considerations

Railway offers a free tier with limited usage. For production use, you'll likely need a paid plan. Check their [pricing page](https://railway.app/pricing) for details. 