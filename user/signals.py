from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import ContactGroup


@receiver(pre_save, sender=ContactGroup)
def update_parent_group(sender, instance: ContactGroup, **kwargs):
    if instance.parent_group:
        ContactGroup.objects.filter(
            parent_group=instance.parent_group
        ).update(parent_group=None)
