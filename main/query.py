from django.conf import settings
from django.db.models import DateTimeField, ExpressionWrapper, F, Value

otp_expiry = ExpressionWrapper(
    F('created_at') + Value(settings.OTP_EXPIRY),
    output_field=DateTimeField()
)
