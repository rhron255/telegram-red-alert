import functools
import io
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from alert_monitor import publish_alert_to_users
from database import (
    add_subscription,
    get_admins,
    get_all_subscriptions,
    get_all_users,
    remove_subscription,
    get_user_subscriptions,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
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
            "/help - Show this help message\n"
            "/test_alert - Test alert message, send a json file with the alert data\n"
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


PROCESSING_ALERT = 1


def process_alert_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("test_alert", start_alert_conversation)],
        states={
            PROCESSING_ALERT: [
                MessageHandler(filters.Document.ALL, process_alert_message)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


@admin_command
async def start_alert_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text(
        "**IMPORTANT**\n\nThis will trigger alerts to all users. If you are not sure, please cancel."
    )
    return PROCESSING_ALERT


@admin_command
async def process_alert_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    file_content: bytearray = await (
        await update.message.document.get_file()
    ).download_as_bytearray()
    data = json.loads(file_content.decode("utf-8-sig"))
    await update.message.reply_text("Alert message received and decoded successfully.")
    await publish_alert_to_users(data, context.bot)
    return ConversationHandler.END


@admin_command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Alert conversation cancelled.\n\nNo alert was triggered."
    )
    return ConversationHandler.END
