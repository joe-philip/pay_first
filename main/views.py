from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SignupAPISerializer

# Create your views here.


class SignupAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = SignupAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request: Request) -> Response:
        request.auth.delete()
        return Response(status=204)
