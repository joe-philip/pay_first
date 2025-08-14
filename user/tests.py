from rest_framework.test import APITestCase

from main.tests import BasicTestsMixin

from .models import ContactGroup

# Create your tests here.

DEFAULT_CONTACT_GROUP_NAME = "Test Contact Group"


class MainTestsMixin(BasicTestsMixin):
    def create_contact_group(self, **kwargs) -> ContactGroup:
        if "name" not in kwargs.get("name"):
            kwargs["name"] = DEFAULT_CONTACT_GROUP_NAME
        if "owner" not in kwargs.get("owner"):
            kwargs["owner"] = self.create_user()
        name = kwargs.pop("name")
        contact_group, _ = ContactGroup.objects.get_or_create(
            name=name, defaults=kwargs
        )
        return contact_group
