from django.urls import path
# from rest_framework.authtoken import views as rest_framework_views

from . import views

urlpatterns = [
    path("signup", views.SignupAPIView.as_view()),
    path(
        "login", views.LoginAPIView.as_view(),
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
    path(
        "meta", views.MetaAPIView.as_view(),
        name="meta"
    ),
    path(
        "forgot_password", views.ForgotPasswordAPIView.as_view(),
        name="forgot_password"
    )
]
