from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import AuthenticationFailed

from main.models import ModuleInfo
from main.models import User as UserModel

from main.models import ModuleInfo

from .validators import is_email_format, user_exists, validate_password

User = get_user_model()


class SignupAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name',
            'username', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True}
        }

    def validate_username(self, value: str) -> str:
        """
        Validates the provided username by ensuring it is in email format and not already taken.

        Args:
            value (str): The username to validate.

        Returns:
            str: The validated and normalized (lowercase) username.

        Raises:
            serializers.ValidationError: If the username is not in a valid email format or already exists.
        """
        value = value.lower()
        if not is_email_format(value):
            raise serializers.ValidationError('Invalid email format')
        if user_exists(username=value):
            raise serializers.ValidationError('User already exists')
        return value

    def validate_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def save(self, **kwargs):
        user = super().save(**kwargs)
        user.set_password(self.validated_data.get('password'))
        user.save()
        return user


class LoginSerializer(AuthTokenSerializer):
    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            return value
        raise serializers.ValidationError('User does not exist')

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username, password=password
            )
            if not user:
                raise AuthenticationFailed(
                    'Invalid credentials', code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True
    )

    def validate_password(self, value: str) -> str:
        user: UserModel = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect old password')
        return value

    def validate_new_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def validate(self, attrs):
        if attrs.get('password') == attrs.get('new_password'):
            raise serializers.ValidationError(
                {
                    "new_password": ['New password cannot be the same as the old password']
                }
            )
        return attrs

    class Meta:
        model = User
        fields = ('password', 'new_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self, **kwargs):
        user: UserModel = self.context['request'].user
        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class MetaAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleInfo
        depth = 1
        exclude = ("created_at", "updated_at")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        value = value.lower()
        if not is_email_format(value):
            raise serializers.ValidationError('Invalid email format')
        if not user_exists(username=value):
            raise serializers.ValidationError('User does not exist')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    _id = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["_id"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid link.")

        if not PasswordResetTokenGenerator().check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired token.")

        user.set_password(attrs["new_password"])
        user.save()
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    _id = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        user = self.context['user']
        if user.email_verified:
            raise serializers.ValidationError("Email is already verified.")
        if not PasswordResetTokenGenerator().check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired token.")
        return attrs

    def save(self, **kwargs) -> UserModel:
        user = self.context['user']
        user.email_verified = True
        user.save()
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        value = value.lower()
        if not is_email_format(value):
            raise serializers.ValidationError('Invalid email format')
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user found with that email.')
        if user.email_verified:
            raise serializers.ValidationError('User already verified.')
        return value
