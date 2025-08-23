from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import ContactGroup, Contacts
from .permissions import IsContactGroupOwner, IsContactOwner
from .serializers import ContactGroupSerializer, ContactsSerializer

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
