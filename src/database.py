import sqlite3
import threading
from typing import Set, Dict, Optional
import logging

from config import SQLITE_DB_PATH

logger = logging.getLogger(__name__)


# Private singleton instance
connections: dict[int, Optional[sqlite3.Connection]] = {}


def get_db(thread_id=threading.get_ident()) -> sqlite3.Connection:
    """Get or create the singleton database connection."""
    if thread_id not in connections:
        connections[thread_id] = sqlite3.connect(SQLITE_DB_PATH)
        _init_tables()
    return connections[thread_id]


def _init_tables() -> None:
    """Initialize database tables if they don't exist."""
    try:
        cursor = get_db().cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                location TEXT,
                PRIMARY KEY (user_id, location)
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER,
                PRIMARY KEY (user_id)
            )
        """
        )
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
            (user_id, location.lower()),
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
            (user_id, location.lower()),
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
            "SELECT location FROM subscriptions WHERE user_id = ?", (user_id,)
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


def get_all_users() -> Set[int]:
    """Get all users."""
    try:
        cursor = get_db().cursor()
        cursor.execute("SELECT user_id FROM subscriptions")
        return {row[0] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return set()


def add_admin(user_id: int) -> bool:
    """Add admin user"""
    try:
        cursor = get_db().cursor()
        cursor.execute(f"INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False


def get_admins() -> Set[int]:
    """Get all admins"""
    try:
        cursor = get_db().cursor()
        cursor.execute("SELECT user_id FROM admins")
        return {row[0] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return set()


def close_db() -> None:
    """Close the database connections."""
    for connection in connections.values():
        if connection:
            connection.close()
    connections.clear()
