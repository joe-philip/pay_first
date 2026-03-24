from django.db.models import IntegerChoices


class OTPTypeChoices(IntegerChoices):
    EMAIL_VERIFICATION = 1, "Email Verification"
    FORGOT_PASSWORD = 2, "Forgot Password"
