FROM python:3.13-slim

WORKDIR /app

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY src/ /app/src/

# Run the bot
CMD ["python", "src/bot.py"] 