from django.db.models import TextChoices


class TypeChoices(TextChoices):
    CREDIT = "Credit", "credit"
    DEBIT = "Debit", "debit"
