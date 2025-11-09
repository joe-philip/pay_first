from re import match

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    CommonPasswordValidator, MinimumLengthValidator, NumericPasswordValidator,
    UserAttributeSimilarityValidator)
from django.core.exceptions import ValidationError

from root.utils.password_validations import PasswordRegexValidator

User = get_user_model()


def is_email_format(value: str) -> bool:
    """
    Checks if the given string matches a basic email format.

    Args:
        value (str): The string to validate as an email address.

    Returns:
        bool: True if the string matches the email format, False otherwise.
    """
    pattern = r'^([a-z]|[0-9]|\.)+@([a-z]|[0-9])+(\.([a-z]|[0-9])+)+$'
    if match(pattern, value):
        return True
    return False


def user_exists(**kwargs):
    """
    Checks if a User object exists in the database matching the given filter criteria.

    Args:
        **kwargs: Arbitrary keyword arguments representing filter conditions for the User model.

    Returns:
        bool: True if a User matching the criteria exists, False otherwise.
    """
    return User.objects.filter(**kwargs).exists()


def validate_password(password: str, user: User = None) -> list:
    validators = {
        CommonPasswordValidator, MinimumLengthValidator,
        NumericPasswordValidator, UserAttributeSimilarityValidator,
        PasswordRegexValidator
    }
    errors = []
    for validator in validators:
        try:
            validator().validate(password, user=user)
        except ValidationError as exc:
            errors.extend(exc.messages)
    return errors
