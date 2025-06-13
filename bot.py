import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set
from dotenv import load_dotenv
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
ALERT_URL = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
POLLING_INTERVAL = 10  # seconds

# Store user subscriptions
user_subscriptions: Dict[int, Set[str]] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f'Hi {user.first_name}! I am your Red Alert Monitor bot.\n\n'
        'Use /subscribe <location> to subscribe to alerts for a specific location.\n'
        'Use /unsubscribe <location> to unsubscribe from a location.\n'
        'Use /list to see your current subscriptions.\n'
        'Use /help to see this message again.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Available commands:\n'
        '/subscribe <location> - Subscribe to alerts for a location\n'
        '/unsubscribe <location> - Unsubscribe from a location\n'
        '/list - List your current subscriptions\n'
        '/help - Show this help message'
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to alerts for a specific location."""
    if not context.args:
        await update.message.reply_text('Please provide a location to subscribe to.')
        return

    user_id = update.effective_user.id
    location = ' '.join(context.args).lower()

    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = set()

    user_subscriptions[user_id].add(location)
    await update.message.reply_text(f'Subscribed to alerts for: {location}')

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from alerts for a specific location."""
    if not context.args:
        await update.message.reply_text('Please provide a location to unsubscribe from.')
        return

    user_id = update.effective_user.id
    location = ' '.join(context.args).lower()

    if user_id in user_subscriptions and location in user_subscriptions[user_id]:
        user_subscriptions[user_id].remove(location)
        await update.message.reply_text(f'Unsubscribed from alerts for: {location}')
    else:
        await update.message.reply_text(f'You were not subscribed to alerts for: {location}')

async def list_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all current subscriptions."""
    user_id = update.effective_user.id
    if user_id not in user_subscriptions or not user_subscriptions[user_id]:
        await update.message.reply_text('You have no active subscriptions.')
        return

    locations = '\n'.join(f'- {loc}' for loc in user_subscriptions[user_id])
    await update.message.reply_text(f'Your current subscriptions:\n{locations}')

async def check_alerts() -> None:
    """Check for new alerts and notify subscribed users."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
        "Referer": "https://www.oref.org.il/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    })

    try:
        # First visit homepage to get cookies
        session.get("https://www.oref.org.il/", timeout=10)
        
        # Get alerts
        response = session.get(ALERT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, dict):
            return

        # Process alerts
        for alert in data.get('data', []):
            alert_location = alert.get('title', '').lower()
            alert_time = alert.get('time', '')
            
            # Notify subscribed users
            for user_id, locations in user_subscriptions.items():
                if any(loc in alert_location for loc in locations):
                    message = f"🚨 Red Alert in {alert_location}\nTime: {alert_time}"
                    try:
                        await application.bot.send_message(chat_id=user_id, text=message)
                    except Exception as e:
                        logger.error(f"Failed to send message to user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")

async def alert_checker() -> None:
    """Background task to check for alerts periodically."""
    while True:
        await check_alerts()
        await asyncio.sleep(POLLING_INTERVAL)

if __name__ == '__main__':
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("list", list_subscriptions))

    # Start the alert checker in the background
    asyncio.create_task(alert_checker())

    # Start the bot
    application.run_polling() 