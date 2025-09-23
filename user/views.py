from django.db.models import Q, QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import (ContactGroup, Contacts, PaymentMethods, Repayments,
                     Transactions)
from .permissions import (IsAdminPaymentMethod, IsContactGroupOwner,
                          IsContactOwner, IsOwnPaymentMethod, IsOwnRepayment,
                          IsOwnTransaction)
from .serializers import (ContactGroupSerializer, ContactsSerializer,
                          PaymentMethodSerializer, RepaymentsSerializer,
                          TransactionsSerializer)

# Create your views here.


class ContactGroupViewSet(ModelViewSet):
    serializer_class = ContactGroupSerializer
    permission_classes = (IsAuthenticated, IsContactGroupOwner)
    search_fields = ("name",)
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[ContactGroup]:
        queryset = ContactGroup.objects.filter(owner=self.request.user)
        if self.request.method == 'GET':
            return queryset.filter(parent_group__isnull=True).order_by('id')
        return queryset


class ContactsViewSet(ModelViewSet):
    serializer_class = ContactsSerializer
    permission_classes = (IsAuthenticated, IsContactOwner)
    search_fields = ("name", "groups__name")
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[Contacts]:
        return Contacts.objects.filter(owner=self.request.user)


class TransactionsViewSet(ModelViewSet):
    serializer_class = TransactionsSerializer
    permission_classes = (IsAuthenticated, IsOwnTransaction)
    search_fields = ("label", "contact__name")
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[Transactions]:
        return Transactions.objects.filter(contact__owner=self.request.user)


class RepymentsViewSet(ModelViewSet):
    serializer_class = RepaymentsSerializer
    permission_classes = (IsAuthenticated, IsOwnRepayment)
    search_fields = (
        "label", "transaction__label",
        "transaction__contact__name"
    )
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[Repayments]:
        return Repayments.objects.filter(transaction__contact__owner=self.request.user)


class PaymentMethodViewSet(ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = (
        IsAuthenticated, IsOwnPaymentMethod | IsAdminPaymentMethod
    )
    search_fields = ("label",)
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[PaymentMethods]:
        return PaymentMethods.objects.filter(
            Q(
                owner=self.request.user
            ) | Q(
                owner__is_superuser=True, is_common=True
            )
        )
