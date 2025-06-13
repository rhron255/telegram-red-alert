import asyncio
import logging
from typing import Dict, Set
import requests
from telegram import Bot
from database import get_all_subscriptions

logger = logging.getLogger(__name__)

def create_session() -> requests.Session:
    """Create and configure a requests session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; Python requests)",
        "Referer": "https://www.oref.org.il/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    })
    return session

async def check_alerts(bot: Bot, session: requests.Session) -> None:
    """Check for new alerts and notify subscribed users."""
    try:
        # First visit homepage to get cookies
        session.get("https://www.oref.org.il/", timeout=10)
        
        # Get alerts
        response = session.get(
            "https://www.oref.org.il/WarningMessages/alert/alerts.json",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, dict):
            return

        # Get all subscriptions
        subscriptions = get_all_subscriptions()

        # Process alerts
        for alert in data.get('data', []):
            alert_location = alert.get('title', '').lower()
            alert_time = alert.get('time', '')
            
            # Notify subscribed users
            for user_id, locations in subscriptions.items():
                if any(loc in alert_location for loc in locations):
                    message = f"🚨 Red Alert in {alert_location}\nTime: {alert_time}"
                    try:
                        await bot.send_message(chat_id=user_id, text=message)
                    except Exception as e:
                        logger.error(f"Failed to send message to user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")

async def start_monitoring(bot: Bot, polling_interval: int = 10) -> None:
    """Start the alert monitoring loop."""
    session = create_session()
    while True:
        await check_alerts(bot, session)
        await asyncio.sleep(polling_interval) 