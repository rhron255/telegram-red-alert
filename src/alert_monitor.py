import json
import logging
import traceback
from collections import defaultdict
from datetime import datetime

import aiohttp
from telegram import Bot
from telegram.ext import CallbackContext

from alert_response import EMPTY_RESPONSE_TEXT, AlertData
from config import DEBUG_FOLDER
from database import get_all_subscriptions
from temporal_cache import TemporalCache

logger = logging.getLogger(__name__)

alerts_handled = defaultdict(lambda: TemporalCache[str]())
handled_ids = TemporalCache[str]()


def create_session() -> aiohttp.ClientSession:
    """Create and configure a requests session."""
    session = aiohttp.ClientSession()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
            "Referer": "https://www.oref.org.il/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }
    )
    return session


def add_alert_to_cache(alert_data: AlertData):
    handled_ids.add(alert_data.id)
    alerts_handled[alert_data.title].add_all(alert_data.locations)


def filter_alerts_to_publish(alert: dict) -> list[str]:
    """Check if the alert should be published."""
    already_handled_alert = alert["id"] in handled_ids
    current_alert_category_location_cache = alerts_handled[alert["title"]]
    return (
        []
        if already_handled_alert
        else [
            location
            for location in alert["data"]
            if location not in current_alert_category_location_cache
        ]
    )


async def get_active_alert(save_data=True) -> dict:
    response = None
    try:
        async with create_session() as session:
            async with session.get(
                "https://www.oref.org.il/WarningMessages/alert/alerts.json", timeout=10
            ) as response:
                response.raise_for_status()

                text = (await response.text()).strip()
                if text == EMPTY_RESPONSE_TEXT or len(text) == 0:
                    return {}
                if text[:].replace("\0", "") == "":
                    return {}
                if "{" not in text:
                    return {}
                if text[0] != "{":
                    json_start = text.index("{")
                    text = text[json_start:].encode("utf-8").decode("utf-8-sig")

                data = json.loads(text)
                logger.info(f"Alert in progress: {data['title']}")
                if save_data:
                    with open(
                        f"{DEBUG_FOLDER}/alert_log_{data['id']}.json",
                        "w",
                    ) as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                return data
    except Exception as e:
        logger.exception(
            f"Error checking alerts: {type(e).__name__}: {e}\n{e.__traceback__}"
        )
        if save_data:
            with open(
                f"{DEBUG_FOLDER}/error_log_{datetime.now().strftime('%d_%m_%y_%H_%M_%S')}.txt",
                "a",
            ) as f:
                content = (
                    response.text if "response" in locals() else "<no response from server>"
                )
                f.write(
                    f"{type(e).__name__}: {e}\n{traceback.format_tb(e.__traceback__)}\n\ncontent: {content}\n\n"
                )
        return {}


async def check_and_publish_alerts(context: CallbackContext) -> None:
    """Check for new alerts and notify subscribed users."""
    raw_data = await get_active_alert()
    if raw_data == {}:
        return

    filtered_locations = filter_alerts_to_publish(raw_data)

    alert = AlertData(
        raw_data["id"],
        raw_data["cat"],
        raw_data["title"],
        filtered_locations,
        raw_data["desc"],
    )

    add_alert_to_cache(alert)

    if len(alert.locations) == 0:
        logger.info(f"No locations to publish for alert {alert.id}, not yet expired...")
        return

    await publish_alert_to_users(alert, context.bot)


async def publish_alert_to_users(alert: AlertData, bot: Bot) -> None:
    # Get all subscriptions
    subscriptions = get_all_subscriptions()

    # Notify subscribed users
    for user_id, locations in subscriptions.items():
        user_locs = [
            loc for loc in alert.locations if any(map(lambda x: x in loc, locations))
        ]
        if any(loc in alert.locations for loc in locations) or "all" in locations:
            message = (
                f"🚨 {alert.title} 🚨"
                + "\n"
                + alert.description
                + "\n\nמיקומים:\n"
                + "\n".join(user_locs)
            )
            try:
                await bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
