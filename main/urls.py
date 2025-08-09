from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

from . import views

urlpatterns = [
    path("signup", views.SignupAPIView.as_view()),
    path(
        "login", rest_framework_views.obtain_auth_token,
        name="login"
    ),
    path("logout", views.LogoutAPIView.as_view(), name="logout"),
    path(
        "change_password", views.ChangePasswordAPIView.as_view(),
        name="change_password"
    ),
    path(
        "profile", views.UserProfileAPIView.as_view(),
        name="profile"
    ),
]
