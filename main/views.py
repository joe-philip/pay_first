from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.transaction import atomic, on_commit
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.cache import cache_page
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from main.choices import OTPTypeChoices
from main.error_codes import MAXIMUM_NUMBER_OF_ATTEMPTS_EXCEEDED
from main.models import OTP, AppSettings, ModuleInfo
from main.models import User as UserModel
from main.tasks import (resend_verification_otp_email,
                        send_forgot_password_otp_email,
                        send_verification_email_task)
from main.utils import is_auth_token_expired
from root.utils.error_codes import EMAIL_NOT_VERIFIED

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
        with atomic():
            user = serializer.save()
            on_commit(
                lambda: send_verification_email_task.delay(user.id)
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
        user.last_login = now()
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


@method_decorator(cache_page(timeout=None, key_prefix="meta_api"), name='dispatch')
class MetaAPIView(RetrieveAPIView):
    serializer_class = MetaAPISerializer

    def get_object(self) -> dict:
        data = {
            "app_settings": AppSettings.objects.last(),
            "modules": ModuleInfo.objects.all()
        }
        return data


class ForgotPasswordAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            username=serializer.validated_data['email'], is_active=True
        ).first()
        attempt = OTP.objects.get_last_attempt_number(
            user=user,
            otp_type=OTPTypeChoices.FORGOT_PASSWORD.value
        )
        if attempt >= settings.OTP_MAX_ATTEMPTS:
            raise ValidationError(
                {
                    "email": ["Too many attempts, please try again after some time."]
                },
                code=MAXIMUM_NUMBER_OF_ATTEMPTS_EXCEEDED
            )
        send_forgot_password_otp_email.delay(user.id)
        return Response(status=204)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)


class EmailVerificationAPI(APIView):
    def post(self, request: Request) -> Response:
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=204)


class ResendVerificationEmailView(APIView):
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["email"]
        attempt = OTP.objects.get_last_attempt_number(
            user=user, otp_type=OTPTypeChoices.EMAIL_VERIFICATION.value
        )
        if attempt >= settings.OTP_MAX_ATTEMPTS:
            raise ValidationError(
                {
                    "email": ["Too many attempts, please try again after some time."]
                },
                code=MAXIMUM_NUMBER_OF_ATTEMPTS_EXCEEDED
            )
        resend_verification_otp_email.delay(
            user.id
        )
        return Response(status=204)
