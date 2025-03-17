# Troubleshooting Guide

This guide provides solutions for common issues you might encounter with the Telegram to SMS Forwarder application.

## Telegram Connection Issues

### Error: "Cannot send requests while disconnected"

This error occurs when the application tries to connect to Telegram but the connection fails or is interrupted.

**Solution:**

1. Reset the Telegram session:
   ```bash
   python3 reset_telegram_session.py
   ```

2. Restart the web application:
   ```bash
   # First, find the process ID
   ps aux | grep web_app.py
   
   # Then kill the process (replace XXXX with the actual process ID)
   kill XXXX
   
   # Start the web application again
   python3 web_app.py
   ```

3. Try logging in again through the web interface.

### Check Telegram Connection

If you're having issues with Telegram connectivity, you can use the connection check script:

```bash
python3 telegram_connection_check.py
```

This script will:
- Verify your API credentials
- Check the database connection
- Test the connection to Telegram servers

## SMS Delivery Issues

### Messages Not Being Sent

If messages are not being forwarded to SMS:

1. Check the forwarder status on the dashboard
2. Verify your SMSC balance using:
   ```bash
   python3 check_smsc_balance.py
   ```

3. Clear any pending messages in the queue:
   ```bash
   python3 clear_message_queue.py
   ```

### Too Many Messages Being Sent

If too many messages are being sent:

1. Check your rate limiting settings in the Settings page
2. Ensure that "Only forward from non-muted chats" is enabled
3. Consider adjusting the daily limit to a lower value

## Database Issues

If you encounter database errors:

1. Make sure the database file exists and is not corrupted
2. Check for disk space issues
3. Ensure the application has write permissions to the database file

## Web Interface Issues

If the web interface is not loading or showing errors:

1. Check if the web application is running:
   ```bash
   ps aux | grep web_app.py
   ```

2. Look for error messages in the terminal where the web application is running
3. Restart the web application if needed

## Forwarder Service Issues

If the forwarder service is not running or keeps crashing:

1. Check the service status on the dashboard
2. Look for error messages in the terminal where the forwarder is running
3. Restart the forwarder service from the dashboard

## Contact Support

If you continue to experience issues after trying these solutions, please contact support with:

1. A description of the issue
2. Any error messages you're seeing
3. Steps you've already taken to try to resolve the issue 