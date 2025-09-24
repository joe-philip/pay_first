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
router.register(
    r"payment_method", views.PaymentMethodViewSet,
    basename="payment_method"
)
router.register(
    r"payment_source", views.PaymentSourceViewSet,
    basename="payment_source"
)

urlpatterns = [
    path("", include(router.urls)),
]
