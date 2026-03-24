from datetime import datetime
from random import randint

from django.conf import settings
from django.db.models import Manager, QuerySet
from django.db.models.functions import Now
from pytz import timezone


class OTPManager(Manager):
    def create_otp_for_user(self, user, otp_type: int):
        existing_otps = self.filter(user=user, validity__gt=Now())
        existing_otp_values = existing_otps.values_list("otp", flat=True)
        new_otp_value = randint(100000, 999999)
        # Keeps iterating until a new OTP value that is not currently existing in DB is got
        while new_otp_value in existing_otp_values:
            new_otp_value = randint(100000, 999999)
        created_at = datetime.now(tz=timezone(settings.TIME_ZONE))
        otp = self.create(
            user=user, otp=new_otp_value,
            otp_type=otp_type,
            created_at=created_at,
            validity=created_at + settings.OTP_EXPIRY
        )
        return otp

    def filter_valid_otps(self) -> QuerySet:
        return self.filter(validity__gt=Now())
