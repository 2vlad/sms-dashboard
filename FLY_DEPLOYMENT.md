# Deploying Telegram to SMS Forwarder on Fly.io

Fly.io is a platform for running full-stack apps and databases close to your users. It's well-suited for Python applications that need to run continuously.

## Prerequisites

1. A GitHub account
2. Install the Fly CLI:
   - macOS: `brew install flyctl`
   - Linux: `curl -L https://fly.io/install.sh | sh`
   - Windows: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`
3. Sign up for Fly.io: `flyctl auth signup` or `flyctl auth login` if you already have an account

## Deployment Steps

### 1. Prepare your project

1. Make sure you have the `fly.toml` file in your project root (already created)
2. Make sure you have a `Procfile` with the following content:
   ```
   web: python web_app.py
   worker: python run_forwarder_service.py
   ```

### 2. Deploy to Fly.io

1. Initialize your Fly.io app:
   ```bash
   flyctl launch
   ```
   - This will create a new app on Fly.io
   - When prompted, select "No" for creating a PostgreSQL database
   - When prompted, select "No" for creating a Redis database
   - When prompted, select "Yes" to deploy now

2. Create a volume for persistent storage:
   ```bash
   flyctl volumes create telegram_data --size 1
   ```

3. Set environment variables:
   ```bash
   flyctl secrets set TELEGRAM_API_ID=your_api_id
   flyctl secrets set TELEGRAM_API_HASH=your_api_hash
   flyctl secrets set SMSC_LOGIN=your_smsc_login
   flyctl secrets set SMSC_PASSWORD=your_smsc_password
   ```
   Add any other environment variables your application needs.

4. Deploy the application:
   ```bash
   flyctl deploy
   ```

### 3. Set up the Forwarder Service

Fly.io doesn't directly support background workers like Railway or Render, but you can run the forwarder as a separate app:

1. Create a new directory for the forwarder:
   ```bash
   mkdir telegram-sms-forwarder-worker
   cd telegram-sms-forwarder-worker
   ```

2. Create a new `fly.toml` file:
   ```toml
   app = "telegram-sms-forwarder-worker"
   primary_region = "iad"
   kill_signal = "SIGINT"
   kill_timeout = 5

   [build]
     builder = "paketobuildpacks/builder:base"

   [env]
     PORT = "8080"

   [processes]
     app = "python run_forwarder_service.py"

   [mounts]
     source = "telegram_data"
     destination = "/app/data"
   ```

3. Copy your project files to this directory (excluding git files):
   ```bash
   cp -r ../* .
   rm -rf .git
   ```

4. Initialize and deploy the worker app:
   ```bash
   flyctl launch
   ```
   - Use a different app name (e.g., telegram-sms-forwarder-worker)
   - When prompted, select "No" for creating databases
   - When prompted, select "Yes" to deploy now

5. Set the same environment variables for the worker app:
   ```bash
   flyctl secrets set TELEGRAM_API_ID=your_api_id
   flyctl secrets set TELEGRAM_API_HASH=your_api_hash
   flyctl secrets set SMSC_LOGIN=your_smsc_login
   flyctl secrets set SMSC_PASSWORD=your_smsc_password
   ```

### 4. Custom Domain (Optional)

1. Add a custom domain to your web app:
   ```bash
   flyctl certs create your-domain.com
   ```

2. Update your DNS settings as instructed by Fly.io

## Monitoring and Logs

1. View logs for your web app:
   ```bash
   flyctl logs
   ```

2. View logs for your worker app:
   ```bash
   flyctl logs -a telegram-sms-forwarder-worker
   ```

3. Monitor your app's status:
   ```bash
   flyctl status
   ```

## Scaling (if needed)

Fly.io allows you to scale your application:

1. Scale horizontally (more instances):
   ```bash
   flyctl scale count 2
   ```

2. Scale vertically (more resources):
   ```bash
   flyctl scale vm shared-cpu-1x
   ```

## Troubleshooting

If you encounter any issues:

1. Check the logs for error messages:
   ```bash
   flyctl logs
   ```

2. SSH into your app for debugging:
   ```bash
   flyctl ssh console
   ```

3. Restart your app:
   ```bash
   flyctl restart
   ```

## Cost Considerations

Fly.io offers a generous free tier that includes:
- Up to 3 shared-cpu-1x 256MB VMs
- 3GB persistent volume storage
- 160GB outbound data transfer

For production use, you may need to upgrade to a paid plan. Check their [pricing page](https://fly.io/docs/about/pricing/) for details. 