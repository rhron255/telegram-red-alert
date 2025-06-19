import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class _Timer:
    def __init__(
        self,
        timeout: float,
        callback: Coroutine[Any, Any, None],
        args: tuple = None,
        kwargs: dict = None,
    ) -> None:
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        logger.debug(
            f"Timer expired, executing {self._callback.__name__} with args {self._args} and kwargs {self._kwargs}"
        )
        if self._args and self._kwargs:
            await self._callback(*self._args, **self._kwargs)
        elif self._args:
            await self._callback(*self._args)
        elif self._kwargs:
            await self._callback(**self._kwargs)
        else:
            await self._callback()

    async def cancel(self):
        self._task.cancel()


class TemporalCache:
    """
    A cache which allows to set an expiry duration for entries in it
    """

    def __init__(self, default_timeout: float = 60) -> None:
        self._lock = asyncio.Lock()
        self._timers = {}
        self.default_timeout = default_timeout
        self._cache = defaultdict(lambda: None)

    async def _pop(self, key: Any):
        async with self._lock:
            await self._timers.pop(key).cancel()
            self._cache.pop(key)

    async def put(self, key: Any, value: Any = None, duration: float = None) -> None:
        async with self._lock:
            if key in self._timers:
                self._timers[key].cancel()
            self._timers[key] = _Timer(
                duration or self.default_timeout, self._pop, (key,)
            )
            self._cache[key] = value

    async def put_dict(self, items: dict[Any, Any], duration: float = None) -> None:
        async with self._lock:
            for key, value in items.items():
                await self.put(key, value, duration)

    async def put_all(self, items: list[Any], duration: float = None) -> None:
        await self.put_dict(dict.fromkeys(items, None), duration)

    async def get(self, key: Any) -> Any:
        async with self._lock:
            return self._cache.get(key)

    async def __contains__(self, key: Any) -> bool:
        async with self._lock:
            return key in self._cache

    async def __delitem__(self, key: Any) -> None:
        async with self._lock:
            self._cache.pop(key)

    async def items(self):
        async with self._lock:
            return self._cache.items()
