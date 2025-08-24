from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r"contact-groups", views.ContactGroupViewSet,
    basename="contact-groups"
)
router.register(
    r"contact", views.ContactsViewSet,
    basename="contact"
)
router.register(
    r"transaction", views.TransactionsViewSet,
    basename="transaction"
)
router.register(
    r"repayment", views.RepymentsViewSet,
    basename="repayment"
)

urlpatterns = [
    path("", include(router.urls)),
]
