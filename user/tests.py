from datetime import datetime

from pytz import timezone
from rest_framework.test import APITestCase

from main.tests import BasicTestsMixin

from .choices import TransactionTypeChoices
from .models import ContactGroup, Contacts, Transactions

# Create your tests here.

DEFAULT_CONTACT_GROUP_NAME = "Test Contact Group"
DEFAULT_CONTACT_SUB_GROUP_NAME = "Test Contact Sub Group"
DEFAULT_CONTACT_NAME = "Test Contact"
DEFAULT_TRANSACTION_NAME = "Test Transaction"
DEFAULT_CREDIT_TRANSACTION_NAME = "Test Credit Transaction"
DEFAULT_DEBIT_TRANSACTION_NAME = "Test Debit Transaction"
DEFAULT_TIMEZONE = timezone("Asia/Calcutta")


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
            contact.groups.add(groups)
            contact.save()
        return contact

    def create_transaction(self, _type: str, **kwargs) -> Transactions:
        kwargs["label"] = kwargs.get("label", DEFAULT_TRANSACTION_NAME)
        kwargs["contact"] = kwargs.get("contact", self.create_contact())
        kwargs["_type"] = _type
        kwargs["amount"] = kwargs.get("amount", 10)
        kwargs["description"] = kwargs.get("description", "")
        kwargs["return_date"] = kwargs.get("return_date")
        kwargs["date"] = kwargs.get("date", datetime.now(tz=DEFAULT_TIMEZONE))
        if (transaction := Transactions.objects.filter(**kwargs)).exists():
            return transaction.first()
        return Transactions.objects.create(**kwargs)

    def create_debit_transaction(self, **kwargs) -> Transactions:
        return self.create_transaction(_type=TransactionTypeChoices.DEBIT.value, **kwargs)

    def create_credit_transaction(self, **kwargs) -> Transactions:
        return self.create_transaction(_type=TransactionTypeChoices.CREDIT.value, **kwargs)


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
        response_data = response.json()
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
        return super().setUp()

    # Create Test Cases Start

    def test_credit_transaction_create_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        response_data = response.data
        assert response.status_code == 201
        assert response_data.get(
            "_type") == TransactionTypeChoices.CREDIT.value

    def test_debit_transaction_create_success(self):
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "return_date": None
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "return_date": None
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "contact": contact.id,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        data = {
            "label": DEFAULT_TRANSACTION_NAME,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        owner = self.token.user
        data = {
            "contact": contact.id,
            "_type": TransactionTypeChoices.CREDIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
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
        owner = self.token.user
        contact = self.create_contact(owner=owner)
        owner = self.token.user
        data = {
            "contact": contact.id,
            "_type": TransactionTypeChoices.DEBIT.value,
            "amount": 10,
            "description": "",
            "return_date": None,
            "date": str(datetime.now(tz=DEFAULT_TIMEZONE)),
        }
        response = self.client.post(
            self.base_url + "/",
            data,
            content_type="application/json",
            **self.headers
        )
        errors = response.data
        assert response.status_code == 400
        assert "label" in errors.get("error")

    def test_credit_transaction_create_withoud_payload(self):
        response = self.client.post(
            self.base_url + "/",
            content_type="application/json",
            **self.headers
        )
        assert response.status_code == 400

    def test_debit_transaction_create_withoud_payload(self):
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
