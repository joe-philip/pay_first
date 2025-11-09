from datetime import datetime, timedelta

from django.conf import settings
from pytz import timezone
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View

from root.utils.error_codes import EMAIL_NOT_VERIFIED

from .models import (ContactGroup, Contacts, PaymentMethods, PaymentSources,
                     Repayments, Transactions)


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


class CanUpdateTransaction(BasePermission):
    """
    Permission class to determine if a transaction can be updated.

    Allows updates (PUT requests) only if:
    - The transaction's `pending_amount` is truthy, or
    - If `pending_amount` is falsy, the transaction's `updated_at` timestamp is not older than 30 days from today.

    Returns False if the transaction has no pending amount and was last updated more than 30 days ago.
    """
    # TODO: Implement test cases to test this functionality

    def has_object_permission(self, request: Request, view: View, obj: Transactions):
        if request.method == "PUT":
            if not bool(obj.pending_amount):
                if (obj.updated_at + timedelta(days=30)) < datetime.now(tz=timezone(settings.TIME_ZONE)):
                    return False
        return True


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


class CanUpdateRepayment(BasePermission):
    """
    Permission class that allows updating a Repayments object only if it was last updated within the past 30 days.

    Methods:
        has_object_permission(request, view, obj):
            Returns True if the request method is not PUT, or if the Repayments object's updated_at timestamp is within 30 days from today.
            Returns False if attempting to update (PUT) and the object was last updated more than 30 days ago.
    """
    # TODO: Implement test cases to test this functionality

    def has_object_permission(self, request: Request, view: View, obj: Repayments):
        if request.method == "PUT":
            if (obj.updated_at + timedelta(days=30)) < datetime.now(tz=timezone(settings.TIME_ZONE)):
                return False
        return True


class IsOwnPaymentMethod(BasePermission):
    """
    Permission class that grants access only if the requesting user is the owner of the payment method.

    Methods:
        has_object_permission(request, view, obj):
            Returns True if the payment method's owner matches the requesting user.
    """

    def has_object_permission(self, request: Request, view: View, obj: PaymentMethods) -> bool:
        return obj.owner == request.user


class IsAdminPaymentMethod(BasePermission):
    """
    Permission class that allows access to a PaymentMethods object only if:
    - The request method is "GET".
    - The owner of the payment method is a superuser.
    - The payment method is marked as common.

    Typically used to restrict read access to common payment methods owned by administrators.
    """

    def has_object_permission(self, request: Request, view: View, obj: PaymentMethods):
        return request.method == "GET" and obj.owner.is_superuser and obj.is_common


class IsOwnPaymentSource(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: PaymentSources) -> bool:
        return obj.owner == request.user


class IsEmailVerified(BasePermission):
    """
    Permission class that grants access only if the requesting user's email is verified.

    Methods:
        has_permission(request, view):
            Returns True if the user's email is verified, False otherwise.
    """
    message = "Email is not verified."
    code = EMAIL_NOT_VERIFIED

    def has_permission(self, request: Request, view: View) -> bool:
        return getattr(request.user, 'email_verified', False)
