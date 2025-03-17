# Deploying Telegram to SMS Forwarder on Render.com

Render.com is a unified cloud platform that makes it easy to deploy your applications. It's similar to Vercel but better suited for Python applications and services that need to run continuously.

## Prerequisites

1. A GitHub account
2. A Render.com account (you can sign up at [render.com](https://render.com) using your GitHub account)

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
   git commit -m "Prepare for Render deployment"
   ```
5. Add your GitHub repository as a remote:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo-name.git
   ```
6. Push the code to GitHub:
   ```bash
   git push -u origin main
   ```

### 2. Deploy to Render.com

#### Option A: Deploy using the render.yaml file (Blueprint)

1. Go to [render.com](https://render.com) and sign in with your GitHub account
2. Click on "New" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file and set up your services
5. Review the configuration and click "Apply"

#### Option B: Deploy services manually

1. Go to [render.com](https://render.com) and sign in with your GitHub account
2. Click on "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure your web service:
   - Name: `telegram-sms-web`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn web_app:app`
5. Click "Create Web Service"
6. Repeat the process for the forwarder service:
   - Click on "New" and select "Background Worker"
   - Connect the same GitHub repository
   - Name: `telegram-sms-forwarder`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run_forwarder_service.py`
7. Click "Create Background Worker"

### 3. Set up Environment Variables

1. In your Render dashboard, select your web service
2. Go to the "Environment" tab
3. Add the following environment variables:
   - `TELEGRAM_API_ID` - Your Telegram API ID
   - `TELEGRAM_API_HASH` - Your Telegram API Hash
   - `SMSC_LOGIN` - Your SMSC login
   - `SMSC_PASSWORD` - Your SMSC password
   - Any other environment variables your application needs
4. Repeat the process for the forwarder service

### 4. Set up Persistent Disk

For your Telegram sessions and database:

1. In your Render dashboard, select your web service
2. Go to the "Disks" tab
3. Click "Add Disk"
4. Configure the disk:
   - Name: `data`
   - Mount Path: `/app/data`
   - Size: 1 GB (or as needed)
5. Click "Save Changes"
6. Repeat the process for the forwarder service, using the same disk name to share data between services

### 5. Custom Domain (Optional)

1. In your Render dashboard, select your web service
2. Go to the "Settings" tab
3. Scroll down to "Custom Domain"
4. Click "Add Custom Domain"
5. Enter your domain and follow the instructions to configure DNS settings

## Continuous Deployment

Render automatically sets up continuous deployment. Any changes pushed to your main branch will trigger a new deployment.

## Monitoring and Logs

1. In your Render dashboard, select a service
2. Go to the "Logs" tab to view real-time logs
3. You can also set up log drains to forward logs to external services

## Scaling (if needed)

Render allows you to scale your application:

1. In your service settings, go to the "Settings" tab
2. Scroll down to "Instance Type"
3. Select a larger instance type as needed

## Troubleshooting

If you encounter any issues:

1. Check the logs for error messages
2. Make sure all environment variables are set correctly
3. Verify that your disk is mounted correctly
4. Try redeploying the service

## Cost Considerations

Render offers a free tier with limited usage. For production use, you'll likely need a paid plan. Check their [pricing page](https://render.com/pricing) for details. 