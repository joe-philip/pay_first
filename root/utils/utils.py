from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.http import base36_to_int


def is_token_expired(token, timeout_seconds=settings.PASSWORD_RESET_TIMEOUT) -> bool:
    """Check if token is expired by comparing embedded timestamp."""
    try:
        ts_b36 = token.split("-")[1]
        ts = base36_to_int(ts_b36)
    except Exception:
        return True  # malformed token

    ts_datetime = datetime(2001, 1, 1) + timedelta(days=ts)
    return timezone.now() - ts_datetime > timedelta(seconds=timeout_seconds)


def get_all_cache_keys(pattern: str = "*") -> list[str]:
    """Retrieve all cache keys matching a given pattern."""
    cache_keys = []
    try:
        cache_keys = cache.keys(pattern)
    except Exception:
        pass
    return cache_keys


def clear_cache(keys: list[str]) -> None:

    for key in keys:
        cache.delete(key)
