import os
import logging
import asyncio
import signal
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from database import get_db, close_db
from handlers import start, help_command, subscribe, unsubscribe, list_subscriptions
from alert_monitor import start_monitoring

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal. Cleaning up...")
    close_db()
    exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database (this will create the connection and tables)
    get_db()

    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("list", list_subscriptions))

    # Start alert monitoring in the background
    asyncio.create_task(start_monitoring(application.bot))

    try:
        # Start the bot
        application.run_polling()
    finally:
        # Ensure database connection is closed
        close_db()

if __name__ == '__main__':
    main() 