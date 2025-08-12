from django.contrib.auth.models import User
from rest_framework.test import APITestCase

# Create your tests here.

# Constants for default user credentials
DEFAULT_PASSWORD = "Paword*1"  # Password of length 8
DEFAULT_USERNAME = "tester@payfirst.com"


class BasicTestsMixin:
    def create_user(self, *args, **kwargs):
        """
        Create a user with the given arguments.
        """
        if "password" not in kwargs:
            kwargs["password"] = DEFAULT_PASSWORD
        if "username" not in kwargs:
            kwargs["username"] = DEFAULT_USERNAME
        return User.objects.create_user(*args, **kwargs)


class SignupAPITestCase(APITestCase, BasicTestsMixin):
    def setUp(self):
        self.BASE_URL = "/signup"
        return super().setUp()

    def test_signup(self):
        """
        Test the signup endpoint.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 201
        ), "Expected status code 201 for successful signup"
        assert User.objects.count() == 1, "Expected one user to be created"
        assert (
            User.objects.get().username == DEFAULT_USERNAME
        ), "Expected username to match the username in payload"  # fmt: off

    def test_username_already_exists(self):
        """
        Test that signup fails if the username already exists.
        """
        self.create_user()
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for existing username"
        assert "username" in response.data.get(
            "error", {}
        ), "Expected 'username' field in error response"

    def test_short_password(self):
        """
        Test that signup fails if the password is too short.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": "short*p",  # Passwords with length of 7 characters
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for short password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_numeric_password(self):
        """
        Test that signup fails if the password is numeric.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": "12345678",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for numeric password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_test_lower_case_password(self):
        """
        Test that signup fails if the password is lowercase.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD.lower(),
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for lowercase password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_test_upper_case_password(self):
        """
        Test that signup fails if the password is uppercase.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD.upper(),
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for uppercase password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_password_without_special_characters(self):
        """
        Test that signup fails if the password does not contain special characters.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for password without special characters"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_payload_without_username(self):
        """
        Test that signup fails if the username is not provided.
        """
        payload = {
            "password": DEFAULT_PASSWORD,
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing username"
        assert "username" in response.data.get(
            "error", {}
        ), "Expected 'username' field in error response"

    def test_payload_without_password(self):
        """
        Test that signup fails if the password is not provided.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_payload_without_first_name(self):
        """
        Test that signup fails if the first name is not provided.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "last_name": "User",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing first name"
        assert "first_name" in response.data.get(
            "error", {}
        ), "Expected 'first_name' field in error response"

    def test_payload_without_last_name(self):
        """
        Test that signup fails if the last name is not provided.
        """
        payload = {
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "first_name": "Test",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 201
        ), "Expected status code 201 for missing last name, since it's not required"
        assert (
            User.objects.filter(last_name="").count() == 1
        ), "Expected one user to be created even without last name"


class LoginAPITestCase(APITestCase, BasicTestsMixin):
    def setUp(self):
        self.BASE_URL = "/login"
        self.user = self.create_user()
        return super().setUp()

    def test_login_success(self):
        """
        Test the login endpoint with valid credentials.
        """
        payload = {
            "username": self.user.username,
            "password": DEFAULT_PASSWORD,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 200
        ), "Expected status code 200 for successful login"
        assert "token" in response.data, "Expected 'token' in response data"

    def test_incorrect_password(self):
        """
        Test the login endpoint with incorrect password.
        """
        payload = {
            "username": self.user.username,
            "password": "wrongpassword",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 401
        ), "Expected status code 400 for incorrect password"

    def test_non_existent_user(self):
        """
        Test the login endpoint with a non-existent user.
        """
        payload = {
            "username": "non_existent_user@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for non-existent user"
        assert "username" in response.data.get(
            "error", {}
        ), "Expected 'username' field in error response"

    def test_missing_username(self):
        """
        Test the login endpoint with a missing username.
        """
        payload = {
            "password": DEFAULT_PASSWORD,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing username"
        assert "username" in response.data.get(
            "error", {}
        ), "Expected 'username' field in error response"

    def test_missing_password(self):
        """
        Test the login endpoint with a missing password.
        """
        payload = {
            "username": DEFAULT_USERNAME,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"
