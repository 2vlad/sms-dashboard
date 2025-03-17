# Telegram to SMS Forwarder - Web Interface

A simple web interface for managing your Telegram to SMS forwarding service. This application allows you to authenticate with your Telegram account, configure your SMS forwarding settings, and monitor your message statistics.

## Features

- **Telegram Authentication**: Securely log in with your Telegram account using the official Telegram API.
- **SMS Configuration**: Set or update the phone number where you want to receive SMS messages.
- **Message Statistics**: View the number of messages forwarded today, this week, and this month.
- **Recent Messages**: See the last 5 messages that were forwarded.
- **Service Status**: Monitor the status of the forwarding service with a visual indicator.
- **Responsive Design**: Works on desktop and mobile devices.

## Prerequisites

- Python 3.7 or higher
- Telegram API credentials (API ID and API Hash)
- SMS provider credentials (configured in your `.env` file)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/telegram-to-sms-forwarder.git
   cd telegram-to-sms-forwarder
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your environment variables:
   - Copy the `.env.example` file to `.env`
   - Fill in your Telegram API credentials and SMS provider details
   - Add a `FLASK_SECRET_KEY` for session security

   Example `.env` additions:
   ```
   FLASK_SECRET_KEY=your_random_secret_key
   ```

## Running the Web Application

1. Start the web server:
   ```
   python web_app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Follow the on-screen instructions to log in with your Telegram account and configure your settings.

## Usage

### First-time Login

1. Enter your Telegram phone number (with country code, e.g., +79123456789).
2. You will receive a verification code in your Telegram app.
3. Enter the verification code on the verification page.
4. If you have Two-Factor Authentication enabled, you'll need to enter your password as well.

### Dashboard

The dashboard provides an overview of your forwarding service:

- **Service Status**: Shows whether the service is running, has an error, or if the status is unknown.
- **Message Statistics**: Displays the number of messages forwarded in different time periods.
- **Recent Messages**: Lists the last 5 messages that were forwarded, including the time, chat name, sender, and message text.

### Settings

In the settings page, you can:

- Update the phone number where you want to receive SMS messages.
- View your Telegram account information.
- Log out of the web application.

## Security Considerations

- The web application uses secure session management.
- Your Telegram session is stored locally and not shared.
- The application does not store your Telegram verification code or 2FA password.
- All database operations are performed using parameterized queries to prevent SQL injection.

## Troubleshooting

If you encounter any issues:

1. Check that your Telegram API credentials are correct.
2. Verify that your SMS provider credentials are valid.
3. Ensure that your phone number is in the correct format (with country code).
4. Check the application logs for any error messages.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon) for the Telegram client library.
- [Flask](https://flask.palletsprojects.com/) for the web framework.
- [Bootstrap](https://getbootstrap.com/) for the UI components. 