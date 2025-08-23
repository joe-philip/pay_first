from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import ContactGroup, Contacts, Transactions
from .permissions import IsContactGroupOwner, IsContactOwner, IsOwnTransaction
from .serializers import (ContactGroupSerializer, ContactsSerializer,
                          TransactionsSerializer)

# Create your views here.


class ContactGroupViewSet(ModelViewSet):
    serializer_class = ContactGroupSerializer
    permission_classes = (IsAuthenticated, IsContactGroupOwner)

    def get_queryset(self) -> QuerySet[ContactGroup]:
        queryset = ContactGroup.objects.filter(owner=self.request.user)
        if self.request.method == 'GET':
            return queryset.filter(parent_group__isnull=True).order_by('id')
        return queryset


class ContactsViewSet(ModelViewSet):
    serializer_class = ContactsSerializer
    permission_classes = (IsAuthenticated, IsContactOwner)

    def get_queryset(self) -> QuerySet[Contacts]:
        return Contacts.objects.filter(owner=self.request.user)


class TransactionsViewSet(ModelViewSet):
    serializer_class = TransactionsSerializer
    permission_classes = (IsAuthenticated, IsOwnTransaction)

    def get_queryset(self) -> QuerySet[Transactions]:
        return Transactions.objects.filter(contact__owner=self.request.user)
