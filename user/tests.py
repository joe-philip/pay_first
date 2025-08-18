from rest_framework.test import APITestCase

from main.tests import BasicTestsMixin

from .models import ContactGroup

# Create your tests here.

DEFAULT_CONTACT_GROUP_NAME = "Test Contact Group"
DEFAULT_CONTACT_SUB_GROUP_NAME = "Test Contact Sub Group"


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
