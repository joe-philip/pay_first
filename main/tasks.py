from datetime import timedelta
from logging import error

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from main.choices import OTPTypeChoices
from main.exceptions import OTPAlreadyExistsException
from main.models import OTP, AppSettings

User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 30},
    retry_backoff=True,
    retry_jitter=True,
)
def send_verification_email_task(self, user_id: int):
    user = User.objects.get(id=user_id)
    otp = OTP.objects.create_otp_for_user(
        user=user,
        otp_type=OTPTypeChoices.EMAIL_VERIFICATION.value,
    )
    app_settings = AppSettings.objects.last()
    app_title = app_settings.app_name if app_settings else "PayBuddy"
    send_mail(
        subject=f"{app_title}: Email Verification",
        message="",
        html_message=render_to_string(
            "email/welcome.html",
            {
                "user": user,
                "otp": otp.otp,
                "expiry": int(settings.OTP_EXPIRY.total_seconds() / 60),
                "app_title": app_title,
            },
        ),
        from_email=None,
        recipient_list=[user.username],
    )


@shared_task(
    bind=True,
    autoretry_for=(OTPAlreadyExistsException,),
    retry_kwargs={"max_retries": 5, "countdown": 30},
    retry_backoff=True,
    retry_jitter=True,
)
def send_forgot_password_otp_email(self, user_id):
    user = User.objects.filter(id=user_id)
    if not user.exists():
        error("Unable to send forgot password email, user not found")
    user = user.first()
    otp = OTP.objects.create_otp_for_user(
        user=user,
        otp_type=OTPTypeChoices.FORGOT_PASSWORD.value
    )
    app_settings = AppSettings.objects.last()
    app_title = app_settings.app_name if app_settings else "PayBuddy"
    send_mail(
        subject=f"{app_title}: Email Verification",
        message="",
        html_message=render_to_string(
            "email/reset_password.html",
            {
                "user": user,
                "otp": otp.otp,
                "expiry": int(settings.OTP_EXPIRY.total_seconds() / 60),
                "app_title": app_title,
            },
        ),
        from_email=None,
        recipient_list=[user.username],
    )
