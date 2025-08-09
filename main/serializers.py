from django.contrib.auth.models import User
from rest_framework import serializers

from .validators import is_email_format, user_exists, validate_password


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


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True
    )

    def validate_password(self, value: str) -> str:
        user: User = self.context['request'].user
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
        user: User = self.context['request'].user
        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')
