from django.urls import path
from rest_framework.urls import urlpatterns

from . import views

urlpatterns = [
    path('signup', views.SignupAPIView.as_view())
]+urlpatterns
