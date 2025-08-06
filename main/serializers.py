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
        raise serializers.ValidationError(value)

    def save(self, **kwargs):
        user = super().save(**kwargs)
        user.set_password(self.validated_data.get('password'))
        user.save()
