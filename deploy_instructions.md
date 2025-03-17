# Deployment Instructions

## Option 1: Deploy on a VPS (Virtual Private Server)

### Prerequisites
- A VPS with Ubuntu/Debian (recommended providers: DigitalOcean, Linode, AWS EC2, etc.)
- SSH access to the server
- Domain name (optional)

### Step 1: Set up the server

1. Connect to your VPS via SSH:
```bash
ssh username@your_server_ip
```

2. Update the system:
```bash
sudo apt update && sudo apt upgrade -y
```

3. Install required packages:
```bash
sudo apt install -y python3 python3-pip python3-venv git supervisor
```

### Step 2: Clone the repository

1. Clone your repository (or upload your files):
```bash
git clone https://github.com/yourusername/sms-1.git
cd sms-1
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Set up environment variables

1. Create a `.env` file:
```bash
nano .env
```

2. Add your environment variables:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
SMSC_LOGIN=your_smsc_login
SMSC_PASSWORD=your_smsc_password
```

### Step 4: Set up Supervisor to keep the application running

1. Create a supervisor configuration file:
```bash
sudo nano /etc/supervisor/conf.d/telegram-sms.conf
```

2. Add the following configuration:
```ini
[program:telegram-sms-web]
command=/home/username/sms-1/venv/bin/python web_app.py
directory=/home/username/sms-1
autostart=true
autorestart=true
stderr_logfile=/home/username/sms-1/web_app.err.log
stdout_logfile=/home/username/sms-1/web_app.out.log
user=username
environment=PATH="/home/username/sms-1/venv/bin:/usr/bin",PYTHONPATH="/home/username/sms-1"

[program:telegram-sms-forwarder]
command=/home/username/sms-1/venv/bin/python debug_forwarder.py
directory=/home/username/sms-1
autostart=true
autorestart=true
stderr_logfile=/home/username/sms-1/forwarder.err.log
stdout_logfile=/home/username/sms-1/forwarder.out.log
user=username
environment=PATH="/home/username/sms-1/venv/bin:/usr/bin",PYTHONPATH="/home/username/sms-1"
```

3. Update the paths and username in the configuration file to match your server setup.

4. Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
```

5. Check the status:
```bash
sudo supervisorctl status
```

### Step 5: Set up Nginx (optional, for web interface)

1. Install Nginx:
```bash
sudo apt install -y nginx
```

2. Create a Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/telegram-sms
```

3. Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_domain.com;  # or your server IP

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/telegram-sms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

5. Set up SSL with Let's Encrypt (optional but recommended):
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

### Step 6: First-time login and setup

1. Access your web interface at `http://your_domain.com` or `http://your_server_ip`
2. Log in with your Telegram account
3. Set your phone number in the settings
4. Start the forwarding service

## Option 2: Deploy using Docker

If you prefer using Docker, follow these steps:

### Step 1: Create a Dockerfile

Create a file named `Dockerfile` in your project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "web_app.py"]
```

### Step 2: Create a docker-compose.yml file

```yaml
version: '3'

services:
  web:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./:/app
    environment:
      - TELEGRAM_API_ID=${TELEGRAM_API_ID}
      - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
      - SMSC_LOGIN=${SMSC_LOGIN}
      - SMSC_PASSWORD=${SMSC_PASSWORD}
    restart: always

  forwarder:
    build: .
    command: python debug_forwarder.py
    volumes:
      - ./:/app
    environment:
      - TELEGRAM_API_ID=${TELEGRAM_API_ID}
      - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
      - SMSC_LOGIN=${SMSC_LOGIN}
      - SMSC_PASSWORD=${SMSC_PASSWORD}
    restart: always
```

### Step 3: Deploy with Docker Compose

```bash
docker-compose up -d
```

## Option 3: Deploy on a Raspberry Pi

A Raspberry Pi is a cost-effective option for running your application 24/7 at home.

1. Set up Raspberry Pi OS on your Raspberry Pi
2. Follow the same steps as the VPS deployment, but on your Raspberry Pi
3. Make sure to set up port forwarding on your router if you want to access the web interface from outside your home network

## Option 4: Deploy on PythonAnywhere

PythonAnywhere is a cloud platform specifically designed for Python applications.

1. Sign up for a PythonAnywhere account
2. Upload your code or clone from GitHub
3. Set up a web app pointing to your Flask application
4. Set up a scheduled task to run your forwarder script

## Option 5: Deploy on Heroku

Heroku is a platform as a service (PaaS) that enables developers to build, run, and operate applications entirely in the cloud.

1. Create a `Procfile` with the following content:
```
web: python web_app.py
worker: python debug_forwarder.py
```

2. Deploy to Heroku using the Heroku CLI or GitHub integration

## Important Security Considerations

1. **Protect your API credentials**: Make sure your `.env` file is not exposed publicly
2. **Use HTTPS**: Always use SSL/TLS for your web interface
3. **Implement authentication**: Consider adding additional authentication for the web interface
4. **Regular updates**: Keep your system and dependencies updated
5. **Backup**: Regularly backup your database and configuration

## Monitoring and Maintenance

1. Set up monitoring to be alerted if the service goes down
2. Check logs regularly for any errors or issues
3. Monitor your SMS provider balance to ensure you don't run out of credits 