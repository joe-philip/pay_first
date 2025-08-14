from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
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
        username = kwargs.pop('username')
        password = kwargs.get('password')
        user, created = User.objects.get_or_create(
            username=username, defaults=kwargs
        )
        if created:
            user.set_password(password)
            user.save()
        return user

    def create_user_token(self, *args, **kwargs):
        """
        Create a user and return the associated token.
        """
        if "user" not in kwargs:
            kwargs["user"] = self.create_user(*args, **kwargs)
        user = kwargs.pop("user")
        token, _ = Token.objects.get_or_create(user=user, defaults=kwargs)
        return token


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


class LogoutAPITestCase(APITestCase, BasicTestsMixin):
    def setUp(self):
        self.BASE_URL = "/logout"
        self.user = self.create_user()
        self.token = self.create_user_token(user=self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    def test_logout_success(self):
        """Test the logout endpoint with a valid token."""
        self.client.credentials(**self.headers)
        response = self.client.delete(self.BASE_URL)
        assert (
            response.status_code == 204
        ), "Expected status code 204 for successful logout"
        assert not Token.objects.filter(
            user=self.user
        ).exists(), "Expected token to be deleted after logout"

    def test_logout_without_token(self):
        """Test the logout endpoint without providing a token."""
        response = self.client.delete(self.BASE_URL)
        assert (
            response.status_code == 401
        ), "Expected status code 401 for unauthorized access"
        assert "error" in response.data, "Expected 'error' field in error response"


class ChangePasswordAPITestCase(APITestCase, BasicTestsMixin):
    def setUp(self):
        self.BASE_URL = "/change_password"
        self.token = self.create_user_token()
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    def test_change_password_success(self):
        """Test changing password with valid credentials."""
        self.client.credentials(**self.headers)
        new_password = "NewPassword*1"
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": new_password,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 204
        ), "Expected status code 204 for successful password change"
        user = User.objects.get(username=self.token.user.username)
        assert user.check_password(
            new_password
        ), "Expected new password to be set correctly"

    def test_change_password_incorrect_old_password(self):
        """Test changing password with incorrect old password."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        payload = {
            "password": "wrongpassword",
            "new_password": DEFAULT_PASSWORD,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for incorrect old password"

    def test_change_password_missing_old_password(self):
        """Test changing password without providing old password."""
        self.client.credentials(**self.headers)
        payload = {
            "new_password": "NewPassword*1",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing old password"
        assert "password" in response.data.get(
            "error", {}
        ), "Expected 'password' field in error response"

    def test_change_password_missing_new_password(self):
        """Test changing password without providing new password."""
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for missing new password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_short_new_password(self):
        """
        Test that changing password fails if the password is too short.
        """
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": "short*p",  # Passwords with length of 7 characters
        }
        self.client.credentials(**self.headers)
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for short password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_numeric_new_password(self):
        """
        Test that changing password fails if the password is numeric.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": "12345678",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for short password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_numeric_new_password(self):
        """
        Test that changing password fails if the password is numeric.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": "12345678",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for short password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_test_lower_case_new_password(self):
        """
        Test that changing password fails if the password is lowercase.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": DEFAULT_PASSWORD.lower(),
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for lowercase password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_test_upper_case_new_password(self):
        """
        Test that changing password fails if the password is uppercase.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": DEFAULT_PASSWORD.upper(),
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for uppercase password"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_new_password_without_special_characters(self):
        """
        Test that changing password fails if the password does not contain special characters.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": "Password123",
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 for password without special characters"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"

    def test_same_old_password_and_new_password(self):
        """
        Test that changing password fails if the old password and new password are same.
        """
        self.client.credentials(**self.headers)
        payload = {
            "password": DEFAULT_PASSWORD,
            "new_password": DEFAULT_PASSWORD,
        }
        response = self.client.post(self.BASE_URL, payload)
        assert (
            response.status_code == 400
        ), "Expected status code 400 when new passowrd and old password are same"
        assert "new_password" in response.data.get(
            "error", {}
        ), "Expected 'new_password' field in error response"


class ProfileAPITestCase(APITestCase, BasicTestsMixin):
    def setUp(self):
        self.BASE_URL = "/profile"
        self.token = self.create_user_token()
        self.headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        return super().setUp()

    def test_profile_api_success(self):
        """
        Tests the profile API endpoint for a successful response.

        This test sends a GET request to the profile API endpoint using the provided headers.
        It asserts that the response status code is 201 (Created) and that the returned username
        matches the username associated with the authentication token.

        Assertions:
            - The response status code is 201.
            - The "username" field in the response data matches the expected username.
        """
        response = self.client.get(self.BASE_URL, **self.headers)
        assert response.status_code == 200, "Expected api status code be 200"
        assert (
            response.data.get("username") == self.token.user.username
        ), f"Expected to be {self.token.user.username}"

    def test_profile_api_without_auth_token(self):
        """
        Test the profile API without providing an authentication token.
        """
        response = self.client.get(self.BASE_URL)
        assert (
            response.status_code == 401
        ), "Expected status code 401 for unauthorized access"
        assert "error" in response.data, "Expected 'error' field in error response"
