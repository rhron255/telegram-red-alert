import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import (
    add_subscription,
    get_admins,
    get_all_subscriptions,
    get_all_users,
    remove_subscription,
    get_user_subscriptions,
)

logger = logging.getLogger(__name__)


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
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! I am your Red Alert Monitor bot.\n\n"
        "Use /subscribe <location> to subscribe to alerts for a specific location.\n"
        "Use /unsubscribe <location> to unsubscribe from a location.\n"
        "Use /list to see your current subscriptions.\n"
        "Use /help to see this message again."
    )


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
            "/help - Show this help message\n"
        )
    else:
        await update.message.reply_text(
            "Available commands:\n"
            "/subscribe <location> - Subscribe to alerts for a location\n"
            "/unsubscribe <location> - Unsubscribe from a location\n"
            "/list - List your current subscriptions\n"
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


@admin_command
async def get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all users"""
    users = get_all_users()
    await update.message.reply_text(f"All users:\n{users}")


@admin_command
async def get_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all subscriptions"""
    subscriptions = "\n".join(
        f"{user_id}: {locations}"
        for user_id, locations in get_all_subscriptions().items()
    )
    await update.message.reply_text(f"All subscriptions:\n{subscriptions}")
