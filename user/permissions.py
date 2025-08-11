from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View


class IsContactGroupOwner(BasePermission):
    """
    Custom permission to only allow owners of a contact group to access it.
    """

    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        # Check if the user is the owner of the contact group
        return obj.owner == request.user
