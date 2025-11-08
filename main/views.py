from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from main.models import ModuleInfo
from main.utils import is_auth_token_expired

from .serializers import (ChangePasswordSerializer, ForgotPasswordSerializer,
                          LoginSerializer, MetaAPISerializer,
                          SignupAPISerializer,
                          UserProfileSerializer)

# Create your views here.


class SignupAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = SignupAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class LoginAPIView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = LoginSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
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

    def get_object(self) -> User:
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
