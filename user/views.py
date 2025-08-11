from django.db.models import Q, QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import ContactGroup
from .permissions import IsContactGroupOwner
from .serializers import ContactGroupSerializer

# Create your views here.


class ContactGroupViewSet(ModelViewSet):
    serializer_class = ContactGroupSerializer
    permission_classes = (IsAuthenticated, IsContactGroupOwner)

    def get_queryset(self) -> QuerySet[ContactGroup]:
        queryset = ContactGroup.objects.filter(owner=self.request.user)
        if self.request.method == 'GET':
            return queryset.filter(parent_group__isnull=True).order_by('id')
        return queryset
