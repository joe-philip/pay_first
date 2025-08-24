from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

from .models import ContactGroup, Contacts, Repayments, Transactions


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


class IsOwnRepayment(BasePermission):
    """
    Permission class to check if the requesting user is the owner of the repayment.

    This permission grants access only if the owner of the contact associated with the repayment's transaction
    matches the current user making the request.

    Methods:
        has_object_permission(request, view, obj): Returns True if the user is the owner of the repayment, False otherwise.

    Args:
        request (Request): The HTTP request object.
        view (View): The view being accessed.
        obj (Repayments): The repayment object being checked.

    Returns:
        bool: True if the user is the owner, False otherwise.
    """
    def has_object_permission(self, request: Request, view: View, obj: Repayments) -> bool:
        return obj.transaction.contact.owner == request.user
