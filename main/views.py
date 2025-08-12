from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from .serializers import (ChangePasswordSerializer, LoginSerializer,
                          SignupAPISerializer, UserProfileSerializer)

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
