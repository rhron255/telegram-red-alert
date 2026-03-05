import datetime
import functools
import logging
from collections import defaultdict
from datetime import timedelta
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

from alert_monitor import get_alert_history
from database import (
    add_subscription,
    get_admins,
    get_all_subscriptions,
    get_all_users,
    remove_subscription,
    get_user_subscriptions,
)

logger = logging.getLogger(__name__)
print = logger.info


def admin_command(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in get_admins():
            await update.message.reply_text(
                "You are not authorized to use this command."
            )
            return
        return await func(update, context)

    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await help_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.effective_user.id in get_admins():
        await update.message.reply_text(
            "Available commands:\n"
            "/subscribe <location> - Subscribe to alerts for a location\n"
            "/unsubscribe <location> - Unsubscribe from a location\n"
            "/list - List your current subscriptions\n"
            "/get_users - Get all users\n"
            "/get_subscriptions - Get all subscriptions\n"
            "/test_alert - Test alert message, send a json file with the alert data\n"
            "/get_active_alerts - Prints out all active alerts\n"
            "/help - Show this help message\n"
        )
    else:
        await update.message.reply_text(
            "Available commands:\n"
            "/subscribe <location> - Subscribe to alerts for a location\n"
            "/unsubscribe <location> - Unsubscribe from a location\n"
            "/list - List your current subscriptions\n"
            "/get_active_alerts - Prints out all active alerts\n"
            "/help - Show this help message\n"
        )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to alerts for a specific location."""
    if not context.args:
        await update.message.reply_text("Please provide a location to subscribe to.")
        return

    user_id = update.effective_user.id
    location = " ".join(context.args).lower()

    if add_subscription(user_id, location):
        logger.info(f"User {user_id} subscribed to alerts for: {location}")
        await update.message.reply_text(f"Subscribed to alerts for: {location}")
    else:
        await update.message.reply_text("Failed to add subscription. Please try again.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from alerts for a specific location."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a location to unsubscribe from."
        )
        return

    user_id = update.effective_user.id
    location = " ".join(context.args).lower()

    if remove_subscription(user_id, location):
        logger.info(f"User {user_id} unsubscribed from alerts for: {location}")
        await update.message.reply_text(f"Unsubscribed from alerts for: {location}")
    else:
        await update.message.reply_text(
            f"You were not subscribed to alerts for: {location}"
        )


async def list_subscriptions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List all current subscriptions."""
    user_id = update.effective_user.id
    locations = get_user_subscriptions(user_id)

    if not locations:
        await update.message.reply_text("You have no active subscriptions.")
        return

    locations_text = "\n".join(f"- {loc}" for loc in locations)
    await update.message.reply_text(f"Your current subscriptions:\n{locations_text}")


async def get_active_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all active alerts"""
    alert_history = (await get_alert_history()).items()
    active_alerts = []
    for time, alerts in alert_history:
        actual_time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now() - actual_time < timedelta(minutes=10):
            active_alerts.extend(alerts)

    if not active_alerts or len(active_alerts) == 0:
        await update.message.reply_text("There are no active alerts at the moment.")
        return

    alerts = defaultdict(list)
    for alert in active_alerts:
        alerts[alert.title] += alert.locations
    for title, locations in alerts.items():
        message_len = len(f"🚨 {title} 🚨\nמיקומים:\n" + "\n".join(locations))
        TELEGRAM_MESSAGE_LIMIT = 1024
        if message_len > TELEGRAM_MESSAGE_LIMIT:
            for i in range(1 + message_len // TELEGRAM_MESSAGE_LIMIT):
                print("HERE")
                await update.message.reply_text(
                    f"🚨 {title} 🚨\nמיקומים:\n"
                    + "\n".join(
                        locations[
                            TELEGRAM_MESSAGE_LIMIT
                            * i : TELEGRAM_MESSAGE_LIMIT
                            * (i + 1)
                        ]
                    )
                )


@admin_command
async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all users"""
    logger.info(f"User: {update.effective_user.id} requested all users")
    users = get_all_users()
    await update.message.reply_text(f"All users:\n{users}")


@admin_command
async def get_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all subscriptions"""
    logger.info(f"User: {update.effective_user.id} requested all subscriptions")
    subscriptions = "\n".join(
        f"{user_id}: {locations}"
        for user_id, locations in get_all_subscriptions().items()
    )
    await update.message.reply_text(f"All subscriptions:\n{subscriptions}")


@admin_command
async def send_message_to_all(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a message to all users"""
    if not context.args:
        await update.message.reply_text("Please provide a message to send.")
        return

    message = " ".join(context.args)
    users = get_all_users()
    success_count = 0
    failure_count = 0

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            failure_count += 1

    await update.message.reply_text(
        f"Message sent to {success_count} users, failed to send to {failure_count} users."
    )
