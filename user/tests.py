from copy import deepcopy
from datetime import datetime

from django.core.management import call_command
from pytest import fixture
from pytz import timezone
from rest_framework.test import APITestCase

from main.tests import BasicTestsMixin

from .choices import TransactionTypeChoices
from .models import (ContactGroup, Contacts, PaymentMethods, PaymentSources, Repayments,
                     Transactions)

# Create your tests here.

DEFAULT_CONTACT_GROUP_NAME = "Test Contact Group"
DEFAULT_CONTACT_SUB_GROUP_NAME = "Test Contact Sub Group"

DEFAULT_CONTACT_NAME = "Test Contact"

DEFAULT_PAYMENT_METHOD_NAME = "Test payment method"
DEFAULT_REPAYMENT_TRANSACTION_REFERENCE_NAME = "Test Transaction"

DEFAULT_TRANSACTION_NAME = "Test Transaction"
DEFAULT_TRANSACTION_TRANSACTION_REFERENCE_NAME = "Test Transaction"

DEFAULT_CREDIT_TRANSACTION_NAME = "Test Credit Transaction"
DEFAULT_DEBIT_TRANSACTION_NAME = "Test Debit Transaction"

DEFAULT_PAYMENT_SOURCE_LABEL = "Test Payment Source"

DEFAULT_TIMEZONE = timezone("Asia/Calcutta")
DEFAULT_REPAYMET_LABEL = "Test Repayment"


@fixture(autouse=True)
def load_fixture(django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata", "main/fixtures/user.json",
            "user/fixtures/payment_methods.json"
        )


class MainTestsMixin(BasicTestsMixin):
    def create_contact_group(self, **kwargs) -> ContactGroup:
        if "name" not in kwargs:
            kwargs["name"] = DEFAULT_CONTACT_GROUP_NAME
        if "owner" not in kwargs:
            kwargs["owner"] = self.create_user()
        name = kwargs.pop("name")
        contact_group, _ = ContactGroup.objects.get_or_create(
            name=name, defaults=kwargs
        )
        return contact_group

    def create_contact(self, **kwargs) -> Contacts:
        groups = kwargs.pop('groups', [])
        kwargs["owner"] = kwargs.get("owner", self.create_user())
        if (contact := Contacts.objects.filter(**kwargs, groups__in=groups)).exists():
            return contact.first()
        contact = Contacts.objects.create(**kwargs)
        if groups:
            contact.groups.add(*groups)
            contact.save()
        return contact

    def create_payment_method(self, **kwargs) -> PaymentMethods:
        if "owner" not in kwargs:
            kwargs["owner"] = self.create_user()
        if "label" not in kwargs:
            kwargs["label"] = DEFAULT_PAYMENT_METHOD_NAME
        if (instance := PaymentMethods.objects.filter(**kwargs)).exists():
            return instance.first()
        return PaymentMethods.objects.create(**kwargs)

    def create_transaction(self, _type: str, **kwargs) -> Transactions:
        kwargs["label"] = kwargs.get("label", DEFAULT_TRANSACTION_NAME)
        kwargs["contact"] = kwargs.get("contact", self.create_contact())
        kwargs["_type"] = _type
        kwargs["amount"] = kwargs.get("amount", 10)
        kwargs["description"] = kwargs.get("description", "")
        kwargs["return_date"] = kwargs.get("return_date")
        kwargs["date"] = kwargs.get("date", datetime.now(tz=DEFAULT_TIMEZONE))
        kwargs["payment_method"] = self.create_payment_method()
        kwargs["transaction_reference"] = kwargs.get(
            "transaction_reference", DEFAULT_TRANSACTION_TRANSACTION_REFERENCE_NAME
        )
        if (transaction := Transactions.objects.filter(**kwargs)).exists():
            return transaction.first()
        return Transactions.objects.create(**kwargs)

    def create_debit_transaction(self, **kwargs) -> Transactions:
        return self.create_transaction(_type=TransactionTypeChoices.DEBIT.value, **kwargs)

    def create_credit_transaction(self, **kwargs) -> Transactions:
        return self.create_transaction(_type=TransactionTypeChoices.CREDIT.value, **kwargs)

    def create_repayment(self, **kwargs) -> Repayments:
        kwargs["label"] = kwargs.get("label", DEFAULT_REPAYMET_LABEL)
        kwargs["transaction"] = kwargs.get(
            "transaction", self.create_credit_transaction()
        )
        kwargs["amount"] = kwargs.get("amount", kwargs['transaction'].amount)
        kwargs["remarks"] = kwargs.get("remarks", "")
        kwargs["payment_method"] = self.create_payment_method()
        kwargs["transaction_reference"] = kwargs.get(
            "transaction_reference", DEFAULT_REPAYMENT_TRANSACTION_REFERENCE_NAME
        )
        if (repaymet := Repayments.objects.filter(**kwargs)).exists():
            return repaymet.first()
        return Repayments.objects.create(**kwargs)

    def create_payment_source(self, **kwargs) -> PaymentSources:
        if (payment_source := PaymentSources.objects.filter(**kwargs)).exists():
            return payment_source.first()
        if not "label" in kwargs:
            kwargs["label"] = DEFAULT_PAYMENT_SOURCE_LABEL
        if not "owner" in kwargs:
            kwargs["owner"] = self.create_user()
        return PaymentSources.objects.create(**kwargs)


class ContactGroupsAPITestCase(APITestCase, MainTestsMixin):
    """
    Contact Groups CRUD API Test cases
    """

    def setUp(self):
        self.base_url = "/user/contact-groups"
        self.token = self.create_user_token()
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    # Create API Test Cases Start

    def test_contact_group_create_success(self):
        parent_group = self.create_contact_group()
        owner = self.token.user
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "parent_group": parent_group.id
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["name"] == DEFAULT_CONTACT_SUB_GROUP_NAME
        assert response.data["owner"] == owner.id
        assert response.data["parent_group"] == parent_group.id

    def test_contact_group_create_without_parent(self):
        owner = self.token.user
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["name"] == DEFAULT_CONTACT_SUB_GROUP_NAME
        assert response.data["owner"] == owner.id

    def test_contact_group_create_with_empty_payload(self):
        data = {}
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    def test_contact_group_create_without_auth_token(self):
        parent_group = self.create_contact_group()
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "parent_group": parent_group.id
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json"
        )
        assert response.status_code == 401

    def test_contact_group_create_with_already_existing_contact_group_name(self):
        parent_group = self.create_contact_group()
        data = {
            "name": DEFAULT_CONTACT_GROUP_NAME,
            "parent_group": parent_group.id,
            **self.headers
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.json()
        print(response_data)
        errors = response_data.get("error")
        assert response.status_code == 400
        assert "name" in errors

    def test_contact_group_create_with_already_existing_contact_group_name_from_other_owner(self):
        other_user = self.create_user(username="other_user@payfirst.com")
        self.create_contact_group(owner=other_user)
        data = {
            "name": DEFAULT_CONTACT_GROUP_NAME
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    # Create API Test Cases End

    # List API Test Cases Start

    def test_contact_group_list_success(self):
        self.create_contact_group()
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_contact_group_search_name_functionality(self):
        # Create multiple contact groups
        self.create_contact_group(name="Alpha Group")
        self.create_contact_group(name="Beta Group")
        self.create_contact_group(name="Gamma Group")
        # Search for 'Beta'
        response = self.client.get(
            self.base_url + "/?search=Beta",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        # Should only return the group with 'Beta' in the name
        assert len(response.data) == 1

    def test_contact_group_case_insensitivity_search_name_functionality(self):
        # Create multiple contact groups
        self.create_contact_group(name="Alpha Group")
        self.create_contact_group(name="Beta Group")
        self.create_contact_group(name="Gamma Group")
        # Search for 'beta'
        response = self.client.get(
            self.base_url + "/?search=beta",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        # Should only return the group with 'Beta' in the name
        assert len(response.data) == 1

    def test_contact_group_search_name_with_invalid_name_functionality(self):
        # Create multiple contact groups
        self.create_contact_group(name="Alpha Group")
        self.create_contact_group(name="Beta Group")
        self.create_contact_group(name="Gamma Group")
        # Search for 'Beta'
        response = self.client.get(
            self.base_url + "/?search=invalid",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        # Should only return the group with 'Beta' in the name
        assert response.data == []

    def test_contact_group_list_with_empty_data(self):
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data == []

    def test_contact_group_list_without_auth_token(self):
        self.create_contact_group()
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json"
        )
        assert response.status_code == 401

    def test_pagination_contact_group_list_success(self):
        owner = self.token.user
        for i in range(15):
            self.create_contact_group(owner=owner, name=f"Group {i+1}")
        response = self.client.get(
            self.base_url + "/?page=2&page_size=5",
            content_type="application/json",
            **self.headers
        )
        print(response.data)
        assert response.status_code == 200
        assert len(response.data.get("results", [])) == 5
        assert response.data.get("results", [])[0]["name"] == "Group 6"
        assert response.data.get("results", [])[-1]["name"] == "Group 10"
        assert response.data['count'] == 15

    # List API Test Cases End

    # Retrieve API Test Cases Start

    def test_retrieve_success(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        response = self.client.get(
            self.base_url + f"/{instance.id}/",
            **self.headers
        )
        response.status_code == 200
        assert response.data.get("id") == instance.id

    def test_retrieve_invalid_pk_success(self):
        owner = self.token.user
        self.create_contact_group(owner=owner)
        response = self.client.get(
            self.base_url + f"/{0}/",
            **self.headers
        )
        assert response.status_code == 404

    def test_retrieve_api_without_auth_token(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        response = self.client.get(
            self.base_url + f"/{instance.id}/"
        )
        response.status_code == 401

    # Retrieve API Test Cases End

    # Update API Test Cases Start

    def test_update_api_success(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        parent_instance = self.create_contact_group(
            name="parent instance", owner=owner)
        data = {
            "name": f"Updated {DEFAULT_CONTACT_SUB_GROUP_NAME}",
            "parent_group": parent_instance.id
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200

    def test_update_api_with_invalid_pk(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        parent_instance = self.create_contact_group(
            name="parent instance", owner=owner
        )
        data = {
            "name": f"Updated {DEFAULT_CONTACT_SUB_GROUP_NAME}",
            "parent_group": parent_instance.id
        }
        response = self.client.put(
            self.base_url + f"/0/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_update_with_same_instance_and_same_parent(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        data = {
            "name": f"Updated {DEFAULT_CONTACT_SUB_GROUP_NAME}",
            "parent_group": instance.id
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "parent_group" in response.data["error"]

    def test_update_with_same_instance_name(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        data = {
            "name": instance.name
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200

    def test_update_with_existing_instance_name(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        second_instance = self.create_contact_group(
            owner=owner, name="Second Group"
        )
        data = {
            "name": second_instance.name
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "name" in response.data.get("error")

    def test_update_with_existing_instance_name_from_other_owner(self):
        owner = self.token.user
        other_owner = self.create_user(username="other_user@payfirst.com")
        instance = self.create_contact_group(owner=owner)
        second_instance = self.create_contact_group(
            owner=other_owner, name="Second Group"
        )
        data = {
            "name": second_instance.name
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert ContactGroup.objects.filter(
            name=second_instance.name
        ).count() == 2

    # Update API Test Cases End

    # Delete API Test Cases Start

    def test_delete_api_success(self):
        owner = self.token.user
        instance = self.create_contact_group(owner=owner)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not ContactGroup.objects.filter(owner=owner).exists()

    def test_delete_api_with_invalid_id(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_delete_api_with_other_owner_instance_id(self):
        other_owner = self.create_user(username="otheruser@payfirst.com")
        instance = self.create_contact_group(owner=other_owner)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_delete_parent_group(self):
        owner = self.token.user
        parent_group = self.create_contact_group(owner=owner)
        instance = self.create_contact_group(
            name=DEFAULT_CONTACT_SUB_GROUP_NAME, parent_group=parent_group
        )
        response = self.client.delete(
            self.base_url + f"/{parent_group.id}/",
            content_type="application/json",
            **self.headers
        )
        instance.refresh_from_db()
        assert response.status_code == 204
        assert instance.parent_group == None

    # Delete API Test Cases End


class ContactsAPITestCase(APITestCase, MainTestsMixin):
    def setUp(self):
        self.base_url = "/user/contact"
        self.token = self.create_user_token()
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    # Create API Test cases start

    def test_contact_create_success(self):
        contact_group = self.create_contact_group()
        owner = self.token.user
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "groups": [contact_group.id],
            "data": {}
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["name"] == DEFAULT_CONTACT_SUB_GROUP_NAME
        assert response.data["owner"] == owner.id

    def test_contact_group_create_without_groups(self):
        owner = self.token.user
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "groups": [],
            "data": {}
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["name"] == DEFAULT_CONTACT_SUB_GROUP_NAME
        assert response.data["owner"] == owner.id

    def test_contact_create_with_empty_payload(self):
        data = {}
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    def test_contact_create_without_auth_token(self):
        contact_group = self.create_contact_group()
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "groups": [contact_group.id],
            "data": {}
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json"
        )
        assert response.status_code == 401

    def test_contact_create_with_already_existing_contact_name(self):
        owner = self.token.user
        parent_group = self.create_contact_group(owner=owner)
        contact = self.create_contact(name=DEFAULT_CONTACT_NAME, owner=owner)
        data = {
            "name": contact.name,
            "groups": [parent_group.id],
            "data": {}
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    def test_contact_create_with_already_existing_contact_name_from_other_owner(self):
        other_user = self.create_user(username="other_user@payfirst.com")
        self.create_contact(owner=other_user)
        data = {
            "name": DEFAULT_CONTACT_SUB_GROUP_NAME,
            "groups": [],
            "data": {}
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    # # Create API Test Cases End

    # # List API Test Cases Start

    def test_contact_list_success(self):
        self.create_contact(owner=self.token.user)
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_contact_list_with_empty_data(self):
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data == []

    def test_contact_search_with_name_functionality(self):
        # Create contacts with different names
        self.create_contact(owner=self.token.user, name="Alice")
        self.create_contact(owner=self.token.user, name="Bob")
        self.create_contact(owner=self.token.user, name="Charlie")
        # Search for 'Bob'
        response = self.client.get(
            self.base_url + "/?search=Bob",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Bob"

    def test_contact_search_with_group_name_functionality(self):
        # Create groups
        group_alpha = self.create_contact_group(
            name="Alpha Group", owner=self.token.user
        )
        group_beta = self.create_contact_group(
            name="Beta Group", owner=self.token.user
        )
        # Create contacts in different groups
        self.create_contact(
            owner=self.token.user,
            name="Alice", groups=[group_alpha]
        )
        self.create_contact(
            owner=self.token.user,
            name="Bob", groups=[group_beta]
        )
        # Search for contacts in 'Beta Group'
        response = self.client.get(
            self.base_url + "/?search=Beta Group",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Bob"

    def test_contact_case_insensitive_search_with_name_functionality(self):
        # Create contacts with different names
        self.create_contact(owner=self.token.user, name="Alice")
        self.create_contact(owner=self.token.user, name="Bob")
        self.create_contact(owner=self.token.user, name="Charlie")
        # Search for 'Bob'
        response = self.client.get(
            self.base_url + "/?search=bob",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Bob"

    def test_contact_case_insensitive_search_with_group_name_functionality(self):
        # Create groups
        group_alpha = self.create_contact_group(
            name="Alpha Group", owner=self.token.user
        )
        group_beta = self.create_contact_group(
            name="Beta Group", owner=self.token.user
        )
        # Create contacts in different groups
        self.create_contact(
            owner=self.token.user,
            name="Alice", groups=[group_alpha]
        )
        self.create_contact(
            owner=self.token.user,
            name="Bob", groups=[group_beta]
        )
        # Search for contacts in 'Beta Group'
        response = self.client.get(
            self.base_url + "/?search=beta group",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Bob"

    def test_contact_group_list_without_auth_token(self):
        self.create_contact(owner=self.token.user)
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json"
        )
        assert response.status_code == 401

    # # List API Test Cases End

    # # Retrieve API Test Cases Start

    def test_retrieve_success(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner)
        response = self.client.get(
            self.base_url + f"/{instance.id}/",
            **self.headers
        )
        response.status_code == 200
        assert response.data.get("id") == instance.id

    def test_retrieve_invalid_pk_success(self):
        owner = self.token.user
        self.create_contact(owner=owner)
        response = self.client.get(
            self.base_url + f"/{0}/",
            **self.headers
        )
        assert response.status_code == 404

    def test_retrieve_api_without_auth_token(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner)
        response = self.client.get(
            self.base_url + f"/{instance.id}/"
        )
        response.status_code == 401

    # # Retrieve API Test Cases End

    # # Update API Test Cases Start

    def test_update_api_success(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner)
        group = self.create_contact_group(
            name="parent instance", owner=owner
        )
        data = {
            "name": "Updaed Contact name",
            "groups": [group.id],
            "data": {}
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200

    def test_contact_update_api_with_invalid_id(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner)
        group = self.create_contact_group(
            name="parent instance", owner=owner
        )
        data = {
            "name": "Updaed Contact name",
            "groups": [group.id],
            "data": {}
        }
        response = self.client.put(
            self.base_url + f"/0/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_update_contact_with_same_instance_name(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner, name=DEFAULT_CONTACT_NAME)
        data = {
            "name": instance.name,
            "groups": [],
            "data": {}
        }
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        print(response.data)
        assert response.status_code == 200

    # # Update API Test Cases End

    # # Delete API Test Cases Start

    def test_contact_delete_api_success(self):
        owner = self.token.user
        instance = self.create_contact(owner=owner)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not ContactGroup.objects.filter(owner=owner).exists()

    def test_contact_delete_api_with_invalid_id(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_contact_delete_api_with_other_owner_instance_id(self):
        other_owner = self.create_user(username="otheruser@payfirst.com")
        instance = self.create_contact_group(owner=other_owner)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404


class TransactionsAPITestCase(APITestCase, MainTestsMixin):
    def setUp(self):
        self.base_url = "/user/transaction"
        self.token = self.create_user_token()
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        self.payload = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": self.create_contact(owner=self.token.user).id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
            "payment_method": self.create_payment_method().id,
            "transaction_reference": DEFAULT_TRANSACTION_TRANSACTION_REFERENCE_NAME
        }
        return super().setUp()

    # Create Test Cases Start

    def test_credit_transaction_create_success(self):
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get(
            "_type"
        ) == TransactionTypeChoices.CREDIT.value

    def test_debit_transaction_create_success(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("_type") == TransactionTypeChoices.DEBIT.value

    def test_credit_transaction_create_withoud_date(self):
        data = deepcopy(self.payload)
        data.pop("date")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("date")

    def test_debit_transaction_create_withoud_date(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("date")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("date")

    def test_credit_transaction_create_without_description(self):
        data = deepcopy(self.payload)
        data.pop("description")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("description") == ""

    def test_credit_transaction_create_without_return_date(self):
        data = deepcopy(self.payload)
        data.pop("date")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("return_date") == None

    def test_debit_transaction_create_without_return_date(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("date")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("return_date") == None

    def test_credit_transaction_create_without_description(self):
        owner = self.token.user
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("description") == ""

    def test_debit_transaction_create_without_description(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get("description") == ""

    def test_credit_transaction_create_without_amount(self):
        data = deepcopy(self.payload)
        data.pop("amount")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "amount" in errors.get("error")

    def test_debit_transaction_create_without_amount(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("amount")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "amount" in errors.get("error")

    def test_credit_transaction_create_without__type(self):
        data = deepcopy(self.payload)
        data.pop("_type")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "_type" in errors.get("error")

    def test_credit_transaction_create_without_contact(self):
        data = deepcopy(self.payload)
        data.pop("contact")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "contact" in errors.get("error")

    def test_debit_transaction_create_without_contact(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("contact")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "contact" in errors.get("error")

    def test_credit_transaction_create_withoud_label(self):
        data = deepcopy(self.payload)
        data.pop("label")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "label" in errors.get("error")

    def test_debit_transaction_create_withoud_label(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("label")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "label" in errors.get("error")

    def test_credit_transaction_create_withoud_payment_method(self):
        data = deepcopy(self.payload)
        data.pop("payment_method")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "payment_method" in errors.get("error")

    def test_debit_transaction_create_withoud_payment_method(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("payment_method")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "payment_method" in errors.get("error")

    def test_credit_transaction_create_without_transaction_reference(self):
        data = deepcopy(self.payload)
        data.pop("transaction_reference")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    def test_debit_transaction_create_withoud_transaction_reference(self):
        data = deepcopy(self.payload)
        data.update(_type=TransactionTypeChoices.DEBIT.value)
        data.pop("transaction_reference")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    def test_transaction_create_withoud_payload(self):
        response = self.client.post(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    # Create API Test cases End

    # List API Test cases Start

    def test_transaction_list_success(self):
        contact = self.create_contact(owner=self.token.user)
        self.create_credit_transaction(contact=contact)
        self.create_debit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_transaction_search_with_label(self):
        contact = self.create_contact(owner=self.token.user)
        self.create_credit_transaction(
            contact=contact, label="Alpha Transaction")
        self.create_debit_transaction(
            contact=contact, label="Beta Transaction")
        response = self.client.get(
            self.base_url + "/?search=Beta Transaction",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["label"] == "Beta Transaction"

    def test_transaction_case_insensitive_search_with_label(self):
        contact = self.create_contact(owner=self.token.user)
        self.create_credit_transaction(
            contact=contact, label="Alpha Transaction")
        self.create_debit_transaction(
            contact=contact, label="Beta Transaction")
        response = self.client.get(
            self.base_url + "/?search=beta transaction",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["label"] == "Beta Transaction"

    def test_transaction_search_with_contact_name(self):
        contact_alpha = self.create_contact(
            owner=self.token.user, name="Alpha Contact")
        contact_beta = self.create_contact(
            owner=self.token.user, name="Beta Contact")
        self.create_credit_transaction(
            contact=contact_alpha, label="Alpha Transaction")
        self.create_debit_transaction(
            contact=contact_beta, label="Beta Transaction")
        response = self.client.get(
            self.base_url + "/?search=Beta Contact",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["contact"] == contact_beta.id

    def test_transaction_case_insensitive_search_with_contact_name(self):
        contact_alpha = self.create_contact(
            owner=self.token.user, name="Alpha Contact")
        contact_beta = self.create_contact(
            owner=self.token.user, name="Beta Contact")
        self.create_credit_transaction(
            contact=contact_alpha, label="Alpha Transaction")
        self.create_debit_transaction(
            contact=contact_beta, label="Beta Transaction")
        response = self.client.get(
            self.base_url + "/?search=beta contact",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["contact"] == contact_beta.id

    def test_transaction_list_with_empty_data(self):
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data == []

    # List API Test Cases End

    # Retrieve API Test Cases Start

    def test_credit_transaction_retrieve_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        instance = self.create_credit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + f"/{instance.id}/",
            **self.headers
        )
        response.status_code == 200
        assert response.data.get("id") == instance.id

    def test_debit_transaction_retrieve_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        instance = self.create_debit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + f"/{instance.id}/",
            **self.headers
        )
        response.status_code == 200
        assert response.data.get("id") == instance.id

    def test_credit_transaction_retrieve_invalid_pk(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        self.create_credit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + f"/{0}/",
            **self.headers
        )
        assert response.status_code == 404

    def test_debit_transaction_retrieve_invalid_pk(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        self.create_debit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + f"/{0}/",
            **self.headers
        )
        assert response.status_code == 404

    def test_transaction_retrieve_api_without_auth_token(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        instance = self.create_debit_transaction(contact=contact)
        response = self.client.get(
            self.base_url + f"/{instance.id}/"
        )
        response.status_code == 401

    # Retrieve API Test Cases End

    # Update API Test Cases Start

    def test_transaction_update_api_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        instance = self.create_credit_transaction(contact=contact)
        data = deepcopy(self.payload)
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200

    def test_transaction_update_api_with_invalid_id(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        self.create_debit_transaction(contact=contact)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
        response = self.client.put(
            self.base_url + f"/0/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Update API Test Cases End

    # Delete API Test Cases Start

    def test_transaction_delete_api_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        instance = self.create_debit_transaction(contact=contact)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not ContactGroup.objects.filter(owner=owner).exists()

    def test_transaction_delete_api_with_invalid_id(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_transaction_delete_api_with_other_owner_instance_id(self):
        other_owner = self.create_user(username="otheruser@payfirst.com")
        other_owner_contact = self.create_contact(owner=other_owner)
        instance = self.create_debit_transaction(contact=other_owner_contact)
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Delete API Test Cases End


class RepaymentAPITestCase(APITestCase, MainTestsMixin):
    def setUp(self):
        self.base_url = "/user/repayment"
        self.token = self.create_user_token()
        contact = self.create_contact(owner=self.token.user)
        self.credit_transaction = self.create_credit_transaction(
            contact=contact
        )
        self.payload = {
            "label": DEFAULT_REPAYMET_LABEL,
            "amount": 5,
            "transaction": self.credit_transaction.id,
            "remarks": "",
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
            "payment_method": self.create_payment_method().id,
            "transaction_reference": DEFAULT_REPAYMENT_TRANSACTION_REFERENCE_NAME
        }
        self.debit_transaction = self.create_debit_transaction(contact=contact)
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    # Create API Test Cases Start

    def test_create_repayment_success(self):
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["label"] == data.get("label")

    def test_create_repayment_with_amount_equal_to_transaction_amount(self):
        data = deepcopy(self.payload)
        data.update(amount=self.credit_transaction.amount)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["label"] == data.get("label")

    def test_create_repayment_with_amount_greater_than_transaction_amount(self):
        data = deepcopy(self.payload)
        data.update(amount=self.credit_transaction.amount+1)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "amount" in errors.get("error")

    def test_create_repayment_without_date(self):
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["date"]

    def test_create_repayment_without_remarks(self):
        data = deepcopy(self.payload)
        data.pop("remarks")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201

    def test_create_repayment_without_transaction(self):
        data = deepcopy(self.payload)
        data.pop("transaction")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "transaction" in errors.get("error")

    def test_create_repayment_without_amount(self):
        data = deepcopy(self.payload)
        data.pop("amount")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "amount" in errors.get("error")

    def test_create_repayment_without_label(self):
        data = deepcopy(self.payload)
        data.pop("label")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "label" in errors.get("error")

    def test_create_repayment_without_payment_method(self):
        data = deepcopy(self.payload)
        data.pop("payment_method")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "payment_method" in errors.get("error")

    def test_create_repayment_without_transaction_reference(self):
        data = deepcopy(self.payload)
        data.pop("transaction_reference")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "transaction_reference" in response.data["error"]

    def test_create_repayment_without_payload(self):
        response = self.client.post(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    # Create API Test Cases End

    # List API Test Cases Start

    def test_list_repayment_success(self):
        self.create_repayment()
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_repayment_label_search(self):
        self.create_repayment(label="Alpha Repayment")
        self.create_repayment(label="Beta Repayment")
        response = self.client.get(
            self.base_url + "/?search=Alpha Repayment",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["label"] == "Alpha Repayment"

    def test_repayment_transaction_label_search(self):
        transaction = self.create_credit_transaction(label="Alpha Transaction")
        self.create_repayment(transaction=transaction)
        response = self.client.get(
            self.base_url + "/?search=Alpha Transaction",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["transaction"] == transaction.id

    def test_repayment_contact_name_search(self):
        contact = self.create_contact(name="Alpha Contact")
        transaction = self.create_credit_transaction(contact=contact)
        self.create_repayment(transaction=transaction)
        response = self.client.get(
            self.base_url + "/?search=Alpha Contact",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_repayment_label_case_insensitive_search(self):
        repayment = self.create_repayment(label="Alpha Repayment")
        response = self.client.get(
            self.base_url + "/?search=alpha repayment",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["label"] == "Alpha Repayment"

    def test_repayment_transaction_label_case_insensitive_search(self):
        transaction = self.create_credit_transaction(label="Alpha Transaction")
        self.create_repayment(transaction=transaction)
        response = self.client.get(
            self.base_url + "/?search=alpha transaction",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["transaction"] == transaction.id

    def test_repayment_contact_name_case_insensitive_search(self):
        contact = self.create_contact(name="Alpha Contact")
        transaction = self.create_credit_transaction(contact=contact)
        self.create_repayment(transaction=transaction)
        response = self.client.get(
            self.base_url + "/?search=alpha contact",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_list_repayment_empty(self):
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data == []

    # List API Test Cases End

    # Retrieve API Test Cases Start

    def test_retrieve_repayment_success(self):
        instance = self.create_repayment()
        response = self.client.get(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data.get("id") == instance.id

    def test_retrieve_repayment_with_invalid_pk(self):
        self.create_repayment()
        response = self.client.get(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Retrieve API Test Cases End

    # Update API Test Cases Start

    def test_update_repayment_success(self):
        instance = self.create_repayment()
        data = deepcopy(self.payload)
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data["label"] == data.get("label")

    def test_update_repayment_with_amount_equal_to_transaction_amount(self):
        instance = self.create_repayment()
        data = deepcopy(self.payload)
        data.update(amount=self.credit_transaction.amount)
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data["label"] == data.get("label")

    def test_update_repayment_with_amount_greater_than_transaction_amount(self):
        instance = self.create_repayment()
        data = deepcopy(self.payload)
        data.update(amount=self.credit_transaction.amount+1)
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "amount" in errors.get("error")

    def test_update_repayment_without_payload(self):
        instance = self.create_repayment()
        response = self.client.put(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    # Update API Test Cases End

    # Delete API Test Cases Start

    def test_transaction_delete_success(self):
        instance = self.create_repayment()
        response = self.client.delete(
            self.base_url + f"/{instance.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not Repayments.objects.filter(id=instance.id).exists()

    def test_transaction_delete_invalid_pk(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404


class PaymentMethodAPITestCase(APITestCase, MainTestsMixin):
    def setUp(self):
        self.base_url = "/user/payment_method"
        self.token = self.create_user_token()
        self.payload = {
            "label": DEFAULT_PAYMENT_METHOD_NAME,
            "is_default": False
        }
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    # Create API Test cases Start

    def test_create_api_success(self):
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["label"] == data.get("label")

    def test_create_api_with_existing_name(self):
        data = deepcopy(self.payload)
        payment_method = self.create_payment_method()
        data.update(label=payment_method.label)
        self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "label" in response.data.get("error", {})

    def test_create_api_with_default_true(self):
        data = deepcopy(self.payload)
        data["is_default"] = True
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["is_default"] is True

    def test_create_api_with_multiple_default_true(self):
        data = deepcopy(self.payload)
        payment_method = self.create_payment_method(
            label="Default 2", is_default=True)
        data["is_default"] = True
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        payment_method.refresh_from_db()
        assert response.status_code == 201
        assert response.data["is_default"] is True
        assert not payment_method.is_default

    def test_create_api_with_default_false(self):
        data = deepcopy(self.payload)
        data["is_default"] = False
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["is_default"] is True

    def test_create_api_without_default(self):
        data = deepcopy(self.payload)
        data.pop("is_default")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "is_default" in response.data["error"]

    # Create API Test cases End

    # List API Test Cases Start

    def test_list_api_success(self):
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    # List API Test Cases End

    # Retrieve API Test Cases Start

    def test_retrieve_success(self):
        response = self.client.get(
            self.base_url + f"/{1}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data.get("id") == 1

    def test_retrieve_invalid_pk(self):
        response = self.client.get(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Retrieve API Test Cases End

    # Update API Test Cases Start

    def test_update_success(self):
        payment_method = self.create_payment_method(
            label="Update Test", is_default=True
        )
        data = deepcopy(self.payload)
        data.update(label="Updated Label", is_default=True)
        response = self.client.put(
            self.base_url + f"/{payment_method.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data["label"] == "Updated Label"
        assert response.data["is_default"] is True

    def test_update_invalid_pk(self):
        data = deepcopy(self.payload)
        response = self.client.put(
            self.base_url + "/0/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_update_default_false(self):
        PaymentMethods.objects.filter(
            owner=self.token.user
        ).update(is_default=False)
        payment_method = self.create_payment_method(
            label="Default False", is_default=True
        )
        data = deepcopy(self.payload)
        data.update(
            label="Default False",
            is_default=False

        )
        response = self.client.put(
            self.base_url + f"/{payment_method.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "is_default" in response.data["error"]

    def test_update_common_payment_method(self):
        data = deepcopy(self.payload)
        response = self.client.put(
            self.base_url + "/1/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 403

    # Update API Test Cases End

    # Delete API Test Cases Start

    def test_delete_success(self):
        payment_method = self.create_payment_method(
            label="Delete Test", is_default=True)
        response = self.client.delete(
            self.base_url + f"/{payment_method.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not PaymentMethods.objects.filter(id=payment_method.id).exists()

    def test_delete_invalid_pk(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    def test_delete_common_payment_method(self):
        response = self.client.delete(
            self.base_url + "/1/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 403

    # Delete API Test Cases End


class PaymentSourcesAPITestCase(APITestCase, MainTestsMixin):
    def setUp(self):
        self.base_url = "/user/payment_source"
        self.token = self.create_user_token()
        self.payload = {
            "label": DEFAULT_PAYMENT_SOURCE_LABEL
        }
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    # Create API Test Case Start

    def test_create_api_success(self):
        data = deepcopy(self.payload)
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 201
        assert response.data["label"] == data["label"]

    def test_create_api_duplicate_label(self):
        data = deepcopy(self.payload)
        # Create once
        payment_source = self.create_payment_source()
        data.update(label=payment_source.label)
        # Try to create again with same label
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "label" in response.data.get("error", {})

    def test_create_api_without_label(self):
        data = deepcopy(self.payload)
        data.pop("label")
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "label" in response.data.get("error", {})

    def test_create_api_without_payload(self):
        response = self.client.post(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    # Create API Test Case End

    # List API Test Case Start

    def test_list_api_success(self):
        self.create_payment_source()
        response = self.client.get(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert len(response.data) == 1

    # List API Test Case End

    # Retrieve API Test Case Start

    def test_retrieve_api_success(self):
        payment_source = self.create_payment_source()
        response = self.client.get(
            self.base_url + f"/{payment_source.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data.get("id") == payment_source.id

    def test_retrieve_api_invalid_pk(self):
        response = self.client.get(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Retrieve API Test Case End

    # Update API Test Case Start

    def test_update_api_success(self):
        payment_source = self.create_payment_source(label="Old Label")
        data = deepcopy(self.payload)
        data.update(label="Updated Label")
        response = self.client.put(
            self.base_url + f"/{payment_source.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 200
        assert response.data["label"] == "Updated Label"

    def test_update_api_with_existing_label(self):
        self.create_payment_source(label="Label1")
        payment_source2 = self.create_payment_source(label="Label2")
        data = deepcopy(self.payload)
        data.update(label="Label1")
        response = self.client.put(
            self.base_url + f"/{payment_source2.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "label" in response.data.get("error", {})

    def test_update_api_without_label(self):
        payment_source = self.create_payment_source(label="Old Label")
        data = deepcopy(self.payload)
        data.pop("label")
        response = self.client.put(
            self.base_url + f"/{payment_source.id}/",
            data,
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400
        assert "label" in response.data.get("error", {})

    # Update API Test Case End

    # Delete API Test Case Start

    def test_delete_api_success(self):
        payment_source = self.create_payment_source(label="Delete Test")
        response = self.client.delete(
            self.base_url + f"/{payment_source.id}/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 204
        assert not PaymentSources.objects.filter(id=payment_source.id).exists()

    def test_delete_api_with_invalid_pk(self):
        response = self.client.delete(
            self.base_url + "/0/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 404

    # Delete API Test Case End
