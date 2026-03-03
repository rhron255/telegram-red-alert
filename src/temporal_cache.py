import logging
from datetime import datetime

from config import CACHE_TIMEOUT

logger = logging.getLogger(__name__)


class _CacheEntry[T]:
    def __init__(self, value: T | None, expiry: float) -> None:
        self.value = value
        self.expiry = expiry
        self.inserted_at = datetime.now()

    def is_expired(self) -> bool:
        return self.expiry + self.inserted_at.timestamp() >= datetime.now().timestamp()


class TemporalCache[T]:
    """
    A cache which allows to set an expiry duration for entries in it
    """

    def __init__(self) -> None:
        self._cache = set[_CacheEntry[T]]()

    def put(self, value: T, duration: float = CACHE_TIMEOUT) -> None:
        self._cache.add(_CacheEntry(value, duration))

    def get(self, value: T) -> T | None:
        for entry in self._cache:
            if entry.value == value and not entry.is_expired():
                return entry.value
            elif entry.value == value:
                self._cache.remove(entry)
                return None
        return None

    def __contains__(self, key: T) -> bool:
        return key in self._cache and not self._cache[key].is_expired()

    def get_all(self) -> list[T]:
        return [entry.value for entry in self._cache if not entry.is_expired()]

    def add_all(self, data: list[T]) -> None:
        for entry in data:
            self.put(entry)
