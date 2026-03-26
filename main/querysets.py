from django.db.models import QuerySet
from django.db.models.functions import Now


class OTPQuerySet(QuerySet):
    def filter_valid_otps(self, **kwargs) -> QuerySet:
        return self.filter(validity__gt=Now()).filter(**kwargs)
