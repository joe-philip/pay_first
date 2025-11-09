from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (PasswordResetTokenGenerator,
                                        default_token_generator)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from main.models import AppSettings, ModuleInfo
from main.models import User as UserModel
from main.utils import is_auth_token_expired
from root.utils.error_codes import EMAIL_NOT_VERIFIED
from root.utils.utils import is_token_expired

from .serializers import (ChangePasswordSerializer,
                          EmailVerificationSerializer,
                          ForgotPasswordSerializer, LoginSerializer,
                          MetaAPISerializer, ResendVerificationEmailSerializer,
                          ResetPasswordSerializer, SignupAPISerializer,
                          UserProfileSerializer)

# Create your views here.

User = get_user_model()


class SignupAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = SignupAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        app_settings = AppSettings.objects.last()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link = settings.EMAIL_VERIFICATION_URL.format(uid=uid, token=token)
        timeout = timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        app_title = "PayBuddy"
        if app_settings:
            app_title = app_settings.app_name

        send_mail(
            subject=f"{app_title}: Email Verification",
            message="",
            html_message=render_to_string(
                "email/welcome.html",
                context={
                    "user": user,
                    "link": link,
                    "expiry": int(timeout.total_seconds() / 36e2),
                    "app_title": app_title
                }
            ),
            from_email=None,
            recipient_list=[user.username]
        )
        return Response(serializer.data, status=201)


class LoginAPIView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = LoginSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not user.email_verified:
            raise PermissionDenied(
                "Email is not verified.", code=EMAIL_NOT_VERIFIED
            )
        token, created = Token.objects.get_or_create(user=user)
        if not created:
            if is_auth_token_expired(token):
                token.delete()
                token = Token.objects.create(user=user)
        user.last_login = datetime.now()
        return Response({'token': token.key})


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request: Request) -> Response:
        request.auth.delete()
        return Response(status=204)


class ChangePasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)


class UserProfileAPIView(RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()

    def get_object(self) -> UserModel:
        return self.request.user


class MetaAPIView(ListAPIView):
    serializer_class = MetaAPISerializer
    queryset = ModuleInfo.objects.filter(is_active=True).order_by('created_at')


class ForgotPasswordAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            username=serializer.validated_data['email'], is_active=True
        ).first()
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = settings.RESET_PASSWORD_URL.format(uid=uid, token=token)
        timeout = timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        send_mail(
            subject="Paybuddy: Password Reset",
            message="",
            html_message=render_to_string(
                "email/reset_password.html",
                context={
                    "user": user,
                    "link": reset_link,
                    "expiry": int(timeout.total_seconds() / 60),
                }
            ),
            from_email=None,
            recipient_list=[user.username]
        )
        return Response(status=204)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=204)


class EmailVerificationAPI(APIView):
    def post(self, request: Request) -> Response:
        uid = force_str(urlsafe_base64_decode(request.data.get("_id")))
        user = User.objects.filter(pk=uid)
        if not user.exists():
            raise ValidationError("Invalid link.")
        user = user.first()
        serializer = EmailVerificationSerializer(
            data=request.data, context={"user": user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)


class ResendVerificationEmailView(APIView):
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(username=serializer.validated_data['email'])
        token = default_token_generator.make_token(user)
        expired = is_token_expired(token)  # 24 hours
        if expired:
            token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = settings.EMAIL_VERIFICATION_URL.format(
            uid=uid, token=token)
        subject = "Verify your email address"
        message = f"Hi {user.username},\nClick below to verify your email:\n{verification_link}"
        expiry = settings.PASSWORD_RESET_TIMEOUT // 3600
        app_title = "PayBuddy"
        app_settings = AppSettings.objects.last()
        if app_settings:
            app_title = app_settings.app_name
        send_mail(
            subject,
            message,
            None,
            [user.username],
            html_message=render_to_string(
                "email/email_verify.html",
                context={
                    "user": user,
                    "link": verification_link,
                    "expiry": expiry,
                    "app_title": app_title
                }
            )
        )
        return Response(status=204)
