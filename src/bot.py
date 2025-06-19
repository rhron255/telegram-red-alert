import functools
import os
import logging
import signal
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from database import add_admin, close_db
from handlers import (
    get_subscriptions,
    get_users,
    process_alert_conversation,
    start,
    help_command,
    subscribe,
    unsubscribe,
    list_subscriptions,
)
from alert_monitor import check_alerts
from config import ALERT_CHECK_INTERVAL, DEV_MODE, SUPERUSER_USER_ID, TELEGRAM_BOT_TOKEN

# Load environment variables
load_dotenv()

# Configure logging


logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal. Cleaning up...")
    close_db()
    exit(0)


def setup():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Add superuser to admins
    add_admin(SUPERUSER_USER_ID)


def main():
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe, has_args=True))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe, has_args=True))
    application.add_handler(CommandHandler("list", list_subscriptions))
    application.add_handler(CommandHandler("get_users", get_users))
    application.add_handler(CommandHandler("get_subscriptions", get_subscriptions))
    if DEV_MODE:
        application.add_handler(process_alert_conversation())
    application.job_queue.run_repeating(check_alerts, interval=ALERT_CHECK_INTERVAL)

    application.run_polling()

    close_db()


if __name__ == "__main__":
    setup()
    main()
