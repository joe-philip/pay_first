from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

from .models import ContactGroup, Contacts, Transactions


class IsContactGroupOwner(BasePermission):
    """
    Custom permission to only allow owners of a contact group to access it.
    """

    def has_object_permission(self, request: Request, view: View, obj: ContactGroup) -> bool:
        # Check if the user is the owner of the contact group
        return obj.owner == request.user


class IsContactOwner(BasePermission):
    """
    Custom permission to only allow owners of a Contacts object to access or modify it.
    """

    def has_object_permission(self, request: Request, view: View, obj: Contacts) -> bool:
        return obj.owner == request.user


class IsOwnTransaction(BasePermission):
    """
    Permission class that grants access only if the requesting user is the owner of the transaction's associated contact.

    Methods:
        has_object_permission(request, view, obj): Returns True if the user making the request is the owner of the contact related to the transaction object.
    """
    def has_object_permission(self, request: Request, view: View, obj: Transactions) -> bool:
        return obj.contact.owner == request.user
