import logging
import time

from config import CACHE_TIMEOUT

logger = logging.getLogger(__name__)


class TemporalCache[T]:
    """
    A cache which allows to set an expiry duration for entries in it
    """

    def __init__(self, timeout: float = CACHE_TIMEOUT) -> None:
        self._timeout = timeout
        self._cache = dict[T, float]()

    def _get_timeout(self) -> float:
        return time.time() + self._timeout

    def add(self, value: T) -> None:
        self._cache[value] = self._get_timeout()

    def __contains__(self, key: T) -> bool:
        expiry_time = self._cache.get(key, None)
        if expiry_time is None:
            return False
        if time.time() >= expiry_time:
            self._cache.pop(key, None)
            return False
        return True

    def get_all(self) -> list[T]:
        now = time.time()
        timed_out_values = [
            value for value, expiry_time in self._cache.items() if now >= expiry_time
        ]
        for value in timed_out_values:
            self._cache.pop(value)
        return list(self._cache.keys())

    def add_all(self, data: list[T]) -> None:
        for entry in data:
            self.add(entry)
