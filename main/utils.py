import re
from datetime import datetime

from django.conf import settings
from django.core.cache import caches
from pytz import timezone
from rest_framework.authtoken.models import Token

from root.utils.utils import get_all_cache_keys


def is_auth_token_expired(token: Token) -> bool:
    token_expiry_date = token.created + settings.AUTH_TOKEN_EXPIRY
    now = datetime.now(tz=timezone(settings.TIME_ZONE))
    return now > token_expiry_date


def clear_meta_api_cache():
    CACHE_KEY_REGEX_PATTERN = r"^cache-api-(0|.+)-0$"
    cache = caches['default']
    pattern_glob = "cache-api-*-0"
    keys = get_all_cache_keys(pattern_glob)
    for key in keys:
        if isinstance(key, bytes):
            key = key.decode()
        if re.match(CACHE_KEY_REGEX_PATTERN, key):
            cache.delete(key)
