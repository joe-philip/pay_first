from django.core.exceptions import ValidationError
from django.db import models

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
