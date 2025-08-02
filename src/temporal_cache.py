import asyncio
from datetime import datetime
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

class _CacheEntry:
    def __init__(self, value: Any, expiry: float) -> None:
        self.value = value
        self.expiry = expiry
        self.inserted_at = datetime.now()

    def is_expired(self) -> bool:
        return self.expiry + self.inserted_at.timestamp() < datetime.now().timestamp()

class TemporalCache:
    """
    A cache which allows to set an expiry duration for entries in it
    """

    def __init__(self, default_timeout: float = 60) -> None:
        self.default_timeout = default_timeout
        self._cache = defaultdict(lambda: None)

    def _pop(self, key: Any):
        pass

    def put(self, key: Any, value: Any = None, duration: float = None) -> None:
        self._cache[key] = _CacheEntry(value, duration or self.default_timeout)

    def get(self, key: Any) -> Any:
        if key in self._cache:
            entry = self._cache[key]
            if entry and not entry.is_expired():
                return entry.value
            else:
                self._pop(key)
                return None
        return None

    def __contains__(self, key: Any) -> bool:
        return key in self._cache and not self._cache[key].is_expired()

    def __delitem__(self, key: Any) -> None:
        if key in self._cache:
            del self._cache[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self.put(key, value)
    
    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    def items(self):
        return {k: v.value for k, v in self._cache.items() if not v.is_expired()}

