"""Rate limiter and cache key behavior."""

import time

from src.ingestion._throttle import RateLimiter, _cache_path


def test_rate_limiter_blocks_over_budget():
    limiter = RateLimiter(rpm=2, name="test")
    limiter._window = 0.3
    start = time.monotonic()
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.25


def test_cache_path_is_stable_and_unique():
    a = _cache_path("https://example.com?x=1")
    b = _cache_path("https://example.com?x=1")
    c = _cache_path("https://example.com?x=2")
    assert a == b
    assert a != c
    assert a.suffix == ".json"
