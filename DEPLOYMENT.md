# Deployment Guide

This guide will help you deploy the SMS Dashboard to Vercel.

## Prerequisites

1. A GitHub account
2. A Vercel account (you can sign up at [vercel.com](https://vercel.com) using your GitHub account)

## Deployment Steps

### 1. Push your code to GitHub

1. Create a new repository on GitHub
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
   git commit -m "Initial commit"
   ```
5. Add your GitHub repository as a remote:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo-name.git
   ```
6. Push the code to GitHub:
   ```bash
   git push -u origin main
   ```

### 2. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with your GitHub account
2. Click on "Add New..." and select "Project"
3. Import your GitHub repository
4. Vercel will automatically detect that it's a Next.js project
5. Configure your project settings (or use the defaults)
6. Click "Deploy"

Vercel will automatically build and deploy your application. Once the deployment is complete, you'll receive a URL where your dashboard is live.

### 3. Custom Domain (Optional)

1. In your Vercel project dashboard, go to "Settings" > "Domains"
2. Add your custom domain and follow the instructions to configure DNS settings

## Continuous Deployment

Vercel automatically sets up continuous deployment. Any changes pushed to your main branch will trigger a new deployment.

## Environment Variables

If your application uses environment variables:

1. Go to your project settings in Vercel
2. Navigate to the "Environment Variables" tab
3. Add your environment variables 