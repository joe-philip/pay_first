from django.db.models import ExpressionWrapper, F, FloatField, Q, QuerySet, Sum
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import (ContactGroup, Contacts, PaymentMethods, PaymentSources,
                     Repayments, Transactions)
from .permissions import (CanUpdateRepayment, CanUpdateTransaction,
                          IsAdminPaymentMethod, IsContactGroupOwner,
                          IsContactOwner, IsEmailVerified, IsOwnPaymentMethod,
                          IsOwnPaymentSource, IsOwnRepayment, IsOwnTransaction)
from .serializers import (ContactGroupSerializer, ContactsSerializer,
                          ImportContactsSerializer, PaymentMethodSerializer,
                          PaymentSourcesSerializer, RepaymentsSerializer,
                          SummarySerializer, TransactionsSerializer)

# Create your views here.


class ContactGroupViewSet(ModelViewSet):
    serializer_class = ContactGroupSerializer
    permission_classes = (
        IsAuthenticated, IsEmailVerified, IsContactGroupOwner
    )
    search_fields = ("name",)
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[ContactGroup]:
        queryset = ContactGroup.objects.filter(owner=self.request.user)
        if self.request.method == 'GET':
            return queryset.filter(parent_group__isnull=True).order_by('id')
        return queryset


class ContactsViewSet(ModelViewSet):
    serializer_class = ContactsSerializer
    permission_classes = (IsAuthenticated, IsEmailVerified, IsContactOwner)
    search_fields = ("name", "groups__name")
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[Contacts]:
        return Contacts.objects.filter(owner=self.request.user)


class TransactionsViewSet(ModelViewSet):
    serializer_class = TransactionsSerializer
    permission_classes = (
        IsAuthenticated, IsEmailVerified,
        IsOwnTransaction, CanUpdateTransaction
    )
    search_fields = ("label", "contact__name")
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[Transactions]:
        return Transactions.objects.filter(contact__owner=self.request.user)


class RepymentsViewSet(ModelViewSet):
    serializer_class = RepaymentsSerializer
    permission_classes = (
        IsAuthenticated, IsEmailVerified,
        IsOwnRepayment, CanUpdateRepayment
    )
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
        IsAuthenticated, IsEmailVerified,
        IsOwnPaymentMethod | IsAdminPaymentMethod
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


class PaymentSourceViewSet(ModelViewSet):
    serializer_class = PaymentSourcesSerializer
    permission_classes = (
        IsAuthenticated, IsEmailVerified, IsOwnPaymentSource
    )
    search_fields = ("label",)
    ordering = ("id",)

    def get_queryset(self) -> QuerySet[PaymentSources]:
        return PaymentSources.objects.filter(owner=self.request.user)


class ImportContactsFromCSVAPI(CreateAPIView):
    permission_classes = (IsAuthenticated, IsEmailVerified)

    def post(self, request: Request) -> Response:
        serializer = ImportContactsSerializer(
            data=request.data,
            context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        status = serializer.save()
        return Response(status, status=201)


class SummaryAPIView(APIView):
    permission_classes = (IsAuthenticated, IsEmailVerified)

    def get(self, request: Request) -> Response:
        contacts = (
            Contacts.objects
            .filter(owner=request.user)
            .annotate(
                total_transaction_amount=Sum("transactions__amount"),
                total_repayment_amount=Sum("transactions__repayments__amount"),
            )
            .annotate(
                pending_amount=ExpressionWrapper(
                    F("total_transaction_amount") -
                    F("total_repayment_amount"),
                    output_field=FloatField(),
                )
            )
            .filter(pending_amount__gt=0)
            .order_by("-pending_amount")
        )
        serializer = SummarySerializer(contacts, many=True)
        return Response(serializer.data)
