"""Shared rate-limiting and lightweight JSON HTTP caching."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

from src.config import settings


class RateLimiter:
    """Sliding-window limiter: at most `rpm` calls per 60 seconds."""

    def __init__(self, rpm: int, name: str = "source") -> None:
        if rpm <= 0:
            raise ValueError("rpm must be positive")
        self.rpm = rpm
        self.name = name
        self._window = 60.0
        self._calls: deque[float] = deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self._calls and now - self._calls[0] >= self._window:
            self._calls.popleft()
        if len(self._calls) >= self.rpm:
            sleep_for = self._window - (now - self._calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            while self._calls and now - self._calls[0] >= self._window:
                self._calls.popleft()
        self._calls.append(time.monotonic())


LIMITERS: dict[str, RateLimiter] = {
    "nflverse": RateLimiter(settings.nflverse_rpm, "nflverse"),
    "cfbd": RateLimiter(settings.cfbd_rpm, "cfbd"),
    "pfr": RateLimiter(settings.pfr_rpm, "pfr"),
}


def get_limiter(source: str) -> RateLimiter:
    """Return a source limiter, defaulting to a conservative 30/min."""
    return LIMITERS.setdefault(source, RateLimiter(30, source))


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.cache_dir / f"{digest}.json"


def _cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age_days = (time.time() - path.stat().st_mtime) / 86400.0
    return age_days < settings.http_cache_ttl_days


def cached_get_json(
    url: str,
    *,
    source: str,
    params: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any] | list[Any]:
    """Rate-limited, cached GET that returns parsed JSON."""
    encoded = urllib.parse.urlencode(params or {})
    full_url = f"{url}?{encoded}" if encoded else url
    path = _cache_path(full_url)
    if not force and _cache_fresh(path):
        return json.loads(path.read_text(encoding="utf-8"))

    get_limiter(source).acquire()
    req = urllib.request.Request(full_url, headers={"User-Agent": settings.user_agent})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = response.read().decode("utf-8")
    path.write_text(payload, encoding="utf-8")
    return json.loads(payload)
