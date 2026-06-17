import json
import time
from dataclasses import dataclass
from typing import Any

from backend.app.config import get_settings


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    """Tiny in-memory TTL cache for demo-friendly backend responses."""

    def __init__(self, default_ttl_seconds: int) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._items: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            self._items.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        if ttl <= 0:
            return
        self._items[key] = CacheEntry(value=value, expires_at=time.monotonic() + ttl)

    def clear(self) -> None:
        self._items.clear()


def build_cache_key(
    category: str,
    params: dict[str, Any],
    query: str,
    target_link: str | None = None,
    dynamic_mode: bool = False,
) -> str:
    payload = {
        "category": category,
        "params": params,
        "query": query,
        "target_link": target_link,
        "dynamic_mode": dynamic_mode,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


widget_response_cache = TTLCache(default_ttl_seconds=get_settings().public_api_cache_ttl_seconds)
