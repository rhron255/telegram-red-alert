import sqlite3
from typing import List, Set, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Private singleton instance
_db_connection: Optional[sqlite3.Connection] = None

def get_db(db_path: str = "data/subscriptions.db") -> sqlite3.Connection:
    """Get or create the singleton database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(db_path)
        _init_tables()
    return _db_connection

def _init_tables() -> None:
    """Initialize database tables if they don't exist."""
    try:
        cursor = get_db().cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                location TEXT,
                PRIMARY KEY (user_id, location)
            )
        ''')
        get_db().commit()
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
        raise

def add_subscription(user_id: int, location: str) -> bool:
    """Add a new subscription for a user."""
    try:
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO subscriptions (user_id, location) VALUES (?, ?)",
            (user_id, location.lower())
        )
        get_db().commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error adding subscription: {e}")
        return False

def remove_subscription(user_id: int, location: str) -> bool:
    """Remove a subscription for a user."""
    try:
        cursor = get_db().cursor()
        cursor.execute(
            "DELETE FROM subscriptions WHERE user_id = ? AND location = ?",
            (user_id, location.lower())
        )
        get_db().commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error removing subscription: {e}")
        return False

def get_user_subscriptions(user_id: int) -> Set[str]:
    """Get all subscriptions for a user."""
    try:
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT location FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )
        return {row[0] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Error getting user subscriptions: {e}")
        return set()

def get_all_subscriptions() -> Dict[int, Set[str]]:
    """Get all subscriptions for all users."""
    try:
        cursor = get_db().cursor()
        cursor.execute("SELECT user_id, location FROM subscriptions")
        subscriptions = {}
        for user_id, location in cursor.fetchall():
            if user_id not in subscriptions:
                subscriptions[user_id] = set()
            subscriptions[user_id].add(location)
        return subscriptions
    except Exception as e:
        logger.error(f"Error getting all subscriptions: {e}")
        return {}

def close_db() -> None:
    """Close the database connection."""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None 