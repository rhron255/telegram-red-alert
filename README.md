# Telegram Red Alert Bot

A Telegram bot that monitors red alerts from the official Home Front Command website and sends notifications to subscribed users based on their location preferences.

## Features

- Subscribe to alerts for specific locations
- Unsubscribe from locations
- List current subscriptions
- Real-time notifications when alerts match your subscribed locations
- Persistent data storage using Docker volumes

## Setup

### Option 1: Direct Installation

1. Create a new Telegram bot using [@BotFather](https://t.me/botfather) and get your bot token

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your bot token:
```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your token
nano .env  # or use your preferred text editor
```

4. Run the bot:
```bash
python src/bot.py
```

### Option 2: Docker Installation

1. Create a new Telegram bot using [@BotFather](https://t.me/botfather) and get your bot token

2. Set up the bot token in one of these ways:

   a. Using environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

   b. Using .env file:
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit the .env file with your token
   nano .env  # or use your preferred text editor
   ```

3. Build and run using Docker Compose:
```bash
docker-compose up -d
```

To view logs:
```bash
docker-compose logs -f
```

To stop the bot:
```bash
docker-compose down
```

To stop the bot and remove all data:
```bash
docker-compose down -v
```

## Environment Configuration

The bot requires a `.env` file with the following configuration:

```env
# Telegram Bot Token (get it from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: Database path (defaults to data/subscriptions.db)
# DB_PATH=custom/path/to/database.db
```

You can copy the `.env.example` file and modify it with your settings:
```bash
cp .env.example .env
```

## Data Persistence

The bot uses Docker volumes to persist data:
- Database is stored in a named volume `telegram-red-alert-data`
- Data persists between container restarts and updates
- To backup data, you can use Docker volume commands:
  ```bash
  # List volumes
  docker volume ls
  
  # Backup volume
  docker run --rm -v telegram-red-alert-data:/source -v $(pwd):/backup alpine tar -czf /backup/backup.tar.gz -C /source .
  
  # Restore volume
  docker run --rm -v telegram-red-alert-data:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* && tar -xzf /backup/backup.tar.gz -C /target"
  ```

## Usage

Start a chat with your bot and use the following commands:

- `/start` - Start the bot and see welcome message
- `/help` - Show available commands
- `/subscribe <location>` - Subscribe to alerts for a specific location
- `/unsubscribe <location>` - Unsubscribe from a location
- `/list` - List your current subscriptions

Example:
```
/subscribe tel aviv
/subscribe jerusalem
/list
/unsubscribe tel aviv
```

## Notes

- The bot checks for new alerts every 10 seconds
- Location names are case-insensitive
- You can subscribe to multiple locations
- Alerts will be sent only if they match your subscribed locations
- When using Docker, the container will automatically restart unless explicitly stopped
- Data is persisted in a Docker volume and survives container restarts
- The bot token can be set via environment variable or .env file 