import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SUPERUSER_USER_ID = int(os.getenv("SUPERUSER_ID"))

ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL"))

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH")
os.env