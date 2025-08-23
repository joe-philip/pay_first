from django.db.models import TextChoices


class TransactionTypeChoices(TextChoices):
    CREDIT = "credit", "Credit"
    DEBIT = "debit", "Debit"
