from datetime import timedelta
from logging import error
from random import randint

from celery import shared_task
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.functions import Now
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from main.exceptions import OTPAlreadyExistsException
from main.models import AppSettings
from main.query import otp_expiry

from .models import OTP, User


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 30},
    retry_backoff=True,
    retry_jitter=True,
)
def send_verification_email_task(self, user_id: int):
    user = User.objects.get(id=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = settings.EMAIL_VERIFICATION_URL.format(uid=uid, token=token)
    timeout = timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
    app_settings = AppSettings.objects.last()
    app_title = app_settings.app_name if app_settings else "PayBuddy"
    send_mail(
        subject=f"{app_title}: Email Verification",
        message="",
        html_message=render_to_string(
            "email/welcome.html",
            {
                "user": user,
                "link": link,
                "expiry": int(timeout.total_seconds() / 3600),
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
    existing_otps = OTP.objects.annotate(
        otp_expiry=otp_expiry
    ).filter(user=user, otp_expiry__lt=Now())
    existing_otp_values = existing_otps.values_list("otp", flat=True)
    new_otp_value = randint(100000, 999999)
    # Keeps iterating until a new OTP value that is not currently existing in DB is got
    while new_otp_value in existing_otp_values:
        new_otp_value = randint(100000, 999999)
    otp = OTP.objects.create(user=user, otp=new_otp_value)
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
