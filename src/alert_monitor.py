import asyncio
from datetime import datetime
import json
import logging
import time
from typing import Dict, Set
import requests
from config import DEBUG_FOLDER
from telegram import Bot
from telegram.ext import CallbackContext
from database import get_all_subscriptions
from alert_response import EMPTY_RESPONSE_TEXT
from temporal_cache import TemporalCache

logger = logging.getLogger(__name__)

alerts_handled = TemporalCache()


def create_session() -> requests.Session:
    """Create and configure a requests session."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
            "Referer": "https://www.oref.org.il/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }
    )
    return session


async def filter_alerts_to_publish(alert: dict) -> list[str]:
    """Check if the alert should be published."""
    if await alerts_handled.get(alert["id"]):
        return []
    if not await alerts_handled.get(alert["title"]):
        return alert["data"]
    return [
        location
        for location in alert["data"]
        if location not in await alerts_handled.get(alert["title"])
    ]


async def check_alerts(context: CallbackContext) -> None:
    """Check for new alerts and notify subscribed users."""
    try:
        session = create_session()

        # First visit homepage to get cookies
        session.get("https://www.oref.org.il/", timeout=10)

        # Get alerts
        response = session.get(
            "https://www.oref.org.il/WarningMessages/alert/alerts.json", timeout=10
        )
        response.raise_for_status()

        if response.text == EMPTY_RESPONSE_TEXT:
            return

        try:
            data = response.json()
        except Exception as e:
            if response.text.strip() == "":
                logger.warning("Received non standard empty response from alerts endpoint.")
                return
            
            decoded_data = response.text.encode("utf-8").decode("utf-8-sig")

            data = json.loads(decoded_data)

        logger.info(f"Alert in progress: {data['title']}")

        await publish_alert_to_users(data, context.bot)

    except Exception as e:
        logger.exception(f"Error checking alerts: {type(e).__name__}: {e}\n{e.__traceback__}")
        with open(f"{DEBUG_FOLDER}/error_log_{datetime.now().strftime('%d_%m_%y_%H:%M:%S')}.txt", "a") as f:
            f.write(f"{type(e).__name__}: {e}\n{e.__traceback__}\n\ncontent: {response.text}\n\n")


async def publish_alert_to_users(alert: dict, bot: Bot) -> None:
    alert_locations = await filter_alerts_to_publish(alert)

    if len(alert_locations) == 0:
        logger.info(
            f"No locations to publish for alert {alert['id']}, not yet expired..."
        )
        return

    await alerts_handled.put(alert["id"], alert)
    await alerts_handled.put(alert["title"], alert_locations)

    # Get all subscriptions
    subscriptions = get_all_subscriptions()

    # Process alerts

    title = alert["title"]
    desc = alert["desc"]

    # Notify subscribed users
    for user_id, locations in subscriptions.items():
        user_locs = [loc for loc in alert_locations if any(map(lambda x: x in loc, locations))]
        if any(loc in alert_locations for loc in locations) or "all" in locations:
            message = (
                f"🚨 {title} 🚨" + "\n" + desc + "\n\nמיקומים:\n" + "\n".join(user_locs)
            )
            try:
                await bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
