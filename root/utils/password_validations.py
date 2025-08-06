from re import search

from django.core.exceptions import ValidationError

REGEX_PATTERNS = {
    ("[A-Z]+", "Atleast One upper case character required"),
    ("[a-z]+", "Atleast One lower case character required"),
    ("[0-9]+", "Atleast One numeric character required"),
    (r"^\S+$", "White Spaces not allowed")
}


class PasswordRegexValidator:
    def __init__(self, *args, **kwargs):
        self.patterns = kwargs.get("patterns", REGEX_PATTERNS)
        self.errors = []

    def validate(self, password: str, user=None):
        for pattern in self.patterns:
            if not search(pattern[0], password):
                self.errors.append(pattern[1])
        if self.errors:
            raise ValidationError(self.errors)
