from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r"contact-groups", views.ContactGroupViewSet,
    basename="contact-groups"
)

urlpatterns = [
    path("", include(router.urls)),
]
