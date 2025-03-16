FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p telegram_sessions flask_sessions data

# Expose port
EXPOSE 5001

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "web_app.py"] 