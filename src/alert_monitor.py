import json
import logging
import traceback
import uuid
from collections import defaultdict, namedtuple
from datetime import datetime
from itertools import groupby

from telegram.ext import CallbackContext

from alert_data import AlertData
from config import DEBUG_FOLDER
from database import get_all_subscriptions
from fetch_from_oref import fetch_data_from_oref
from temporal_cache import TemporalCache

logger = logging.getLogger(__name__)

alerts_handled = defaultdict(lambda: TemporalCache[str]())
handled_ids = set()
"""
Pikud ha'oref suck, so they don't necessarily clear the last alert? This happened once, but now it means this cache can't be temporary...
"""
DebugData = namedtuple("DebugData", ["file", "data"])


def add_alert_to_cache(alert_data: AlertData):
    handled_ids.add(alert_data.id)
    alerts_handled[alert_data.title].add_all(alert_data.locations)


async def get_active_alert(save_data=True) -> AlertData | None:
    debug_data: DebugData | None = None
    try:
        data = await fetch_data_from_oref(save_data, "alerts.json")
        if not data or data["id"] in handled_ids:
            return None

        logger.info(
            f"Alert '{data['title']}' with ID: {data['id']} in progress, number of locations: {len(data['data'])}"
        )

        current_alert_category_location_cache = alerts_handled[data["title"]]
        filtered_locations = [
            location
            for location in data["data"]
            if location not in current_alert_category_location_cache
        ]

        if len(filtered_locations) == 0:
            return None

        debug_data = DebugData(
            f"{DEBUG_FOLDER}/alert_log_{data['id']}.json",
            json.dumps(data, ensure_ascii=False, indent=4),
        )

        return AlertData(
            data["id"],
            data["cat"],
            data["title"],
            filtered_locations,
            data["desc"],
        )
    except Exception as e:
        logger.exception(
            f"Error checking alerts: {type(e).__name__}: {e}\n{e.__traceback__}"
        )
        debug_data = DebugData(
            f"{DEBUG_FOLDER}/error_log_{datetime.now().strftime('%d_%m_%y_%H_%M_%S')}.txt",
            f"{type(e).__name__}: {e}\n{traceback.format_tb(e.__traceback__)}\n\ncontent: {'\n'.join(
                e.__notes__)}\n",
        )
        return None
    finally:
        if save_data and debug_data:
            with open(debug_data.file, "w") as f:
                f.write(debug_data.data)


async def get_alert_history() -> dict[str, list[AlertData]]:
    """
    Fetches alert history data and parses it into AlertData.
    The lists will usually be 1 length lists, but I can't ensure that due to the unknown behavior of the API.
    """
    data: list[dict[str, str]] = await fetch_data_from_oref(
        False, "History/AlertsHistory.json"
    )
    if not data:
        return {}
    key_func = lambda x: x["alertDate"]
    grouped_data = {
        key: list(group) for key, group in groupby(sorted(data, key=key_func), key_func)
    }

    all_alerts: dict[str, list[AlertData]] = {}
    for date, alerts in grouped_data.items():
        parsed_alerts: dict[str, AlertData] = {}
        for alert in alerts:
            if alert["title"] not in parsed_alerts:
                parsed_alerts[alert["title"]] = AlertData(
                    uuid.uuid4().hex,
                    alert["category"],
                    alert["title"],
                    [alert["data"]],
                    alert["title"],
                )
            else:
                parsed_alerts[alert["title"]].locations.append(alert["data"])
        all_alerts[date] = list(parsed_alerts.values())
    return all_alerts


async def check_and_publish_alerts(context: CallbackContext) -> None:
    """Check for new alerts and notify subscribed users."""
    global handled_ids
    if len(handled_ids) > 1024:
        handled_ids = handled_ids[:1024]
    alert = await get_active_alert()
    if alert is None:
        return

    add_alert_to_cache(alert)

    if len(alert.locations) == 0:
        logger.info(f"No locations to publish for alert {alert.id}, not yet expired...")
        return

    # Notify subscribed users
    for user_id, locations in get_all_subscriptions().items():
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
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
