FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p telegram_sessions flask_sessions data
EXPOSE 5001
ENV PYTHONUNBUFFERED=1
ENV PRODUCTION=true
ENV PORT=5001
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD curl -f http://localhost:$PORT/test_endpoint || exit 1
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 "web_app:app"
