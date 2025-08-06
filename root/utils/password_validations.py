from re import search

from django.core.exceptions import ValidationError

REGEX_PATTERNS = {
    ("[A-Z]+", "Atleast One upper case character required"),
    ("[a-z]+", "Atleast One lower case character required"),
    ("[0-9]+", "Atleast One numeric character required"),
    (r"^\S+$", "White Spaces not allowed")
}


class PasswordRegexValidator:
    """
    PasswordRegexValidator validates a password against a set of regular expression patterns.

    Attributes:
        patterns (list): A list of tuples where each tuple contains a regex pattern and an associated error message.
        errors (list): A list to store error messages for failed validations.

    Methods:
        __init__(*args, **kwargs):
            Initializes the validator with provided patterns or defaults to REGEX_PATTERNS.

        validate(password: str, user=None):
            Validates the given password against all patterns.
            Appends error messages for each failed pattern.
            Raises ValidationError with all collected errors if any pattern fails.
    """
    def __init__(self, *args, **kwargs):
        self.patterns = kwargs.get("patterns", REGEX_PATTERNS)
        self.errors = []

    def validate(self, password: str, user=None):
        """
        Validates the given password against a set of predefined patterns.

        Args:
            password (str): The password string to validate.
            user (optional): The user object associated with the password (not used in validation).

        Raises:
            ValidationError: If the password does not match one or more patterns,
            with a list of error messages describing the failed validations.
        """
        for pattern in self.patterns:
            if not search(pattern[0], password):
                self.errors.append(pattern[1])
        if self.errors:
            raise ValidationError(self.errors)
