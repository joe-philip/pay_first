from datetime import datetime

from django.conf import settings
from pytz import timezone
from rest_framework.authtoken.models import Token


def is_auth_token_expired(token: Token) -> bool:
    token_expiry_date = token.created + settings.AUTH_TOKEN_EXPIRY
    now = datetime.now(tz=timezone(settings.TIME_ZONE))
    return now > token_expiry_date
