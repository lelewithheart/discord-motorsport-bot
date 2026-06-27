# Use Python 3.11 slim for smaller image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY bot/ ./bot/

# Environment variables
ENV PYTHONPATH=/app/src:${PYTHONPATH}
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "-m", "bot.main"]
