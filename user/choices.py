from django.db.models import TextChoices


class TypeChoices(TextChoices):
    CREDIT = "credit", "Credit"
    DEBIT = "debit", "Debit"
