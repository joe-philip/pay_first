from django.core.exceptions import ValidationError
from django.db import models

from user.choices import TransactionTypeChoices

# Create your models here.


def validate_contact_data_is_json_format(value) -> None:
    if not isinstance(value, dict):
        raise ValidationError("Invalid format json")


class ContactGroup(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="contact_groups"
    )
    parent_group = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subgroups"
    )

    class Meta:
        db_table = 'contact_groups'
        verbose_name = 'Contact Group'
        unique_together = ("name", "owner")

    def __str__(self): return self.name


class Contacts(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    data = models.JSONField(
        default=dict,
        validators=[validate_contact_data_is_json_format]
    )
    groups = models.ManyToManyField(ContactGroup, related_name="contacts")

    class Meta:
        db_table = "contacts"
        verbose_name = "Contact"

    def __str__(self) -> str:
        return self.name


class Transactions(models.Model):
    label = models.CharField()
    contact = models.ForeignKey(
        Contacts,
        related_name="transactions",
        on_delete=models.CASCADE
    )
    _type = models.CharField(choices=TransactionTypeChoices.choices)
    amount = models.FloatField()
    description = models.TextField(blank=True)
    return_date = models.DateTimeField(null=True)
    date = models.DateTimeField(auto_now=True)

    @property
    def pending_amount(self) -> float:
        paid_amount = sum(
            self.repayments.all().values_list("amount", flat=True)
        )
        return self.amount - paid_amount

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"

    def __str__(self) -> str: return self.label


class Repayments(models.Model):
    label = models.CharField()
    transaction = models.ForeignKey(
        Transactions, related_name="repayments", on_delete=models.CASCADE
    )
    amount = models.FloatField()
    remarks = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        total_paid_amount = sum(
            Repayments.objects.filter(
                transaction=self.transaction
            ).exclude(id=self.id).values_list("amount", flat=True)
        )
        pending_amount = self.transaction.amount - total_paid_amount
        if pending_amount == 0:
            raise ValidationError(
                {
                    "amount": ["You do not have any amounts pending in this transaction"]
                }
            )
        if self.amount > pending_amount:
            raise ValidationError(
                {
                    "amount": [f"The amount you entered exceeds the pending amount of {pending_amount}"]
                }
            )
        return super().clean()

    class Meta:
        db_table = "repayments"
        verbose_name = "Repayment"

    def __str__(self) -> str: return self.label

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PaymentMethods(models.Model):
    label = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)
    is_common = models.BooleanField(default=False)
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    class Meta:
        db_table = "payment_methods"
        verbose_name = "Payment method"

    def __str__(self) -> str: return self.label
