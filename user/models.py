from django.db import models

# Create your models here.


class ContactGroup(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='contact_groups'
    )
    parent_group = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subgroups'
    )

    class Meta:
        db_table = 'contact_groups'
        verbose_name = 'Contact Group'
        unique_together = ("name", "owner")

    def __str__(self): return self.name
