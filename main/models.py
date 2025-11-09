from django.contrib.auth.models import AbstractUser
from django.db import models

from root.utils.models import MetaModel

# Create your models here.


class User(AbstractUser):
    email_verified = models.BooleanField(default=False)

    def __str__(self) -> str: return self.username


class AppSettings(MetaModel):
    icon = models.ImageField(upload_to="app/icons/", null=True, blank=True)
    app_name = models.CharField(max_length=50)
    version = models.CharField(max_length=10)
    tag = models.CharField(max_length=50, help_text="Commit hash on tag")
    change_log = models.TextField()
    terms_and_conditions = models.TextField()

    class Meta:
        db_table = "app_settings"
        verbose_name = "App setting"


class ModuleInfo(MetaModel):
    name = models.CharField(max_length=100)
    name_plural = models.CharField(max_length=110, null=True, blank=True)
    model = models.OneToOneField(
        "contenttypes.ContentType",
        related_name="module_info",
        on_delete=models.CASCADE
    )
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "module_info"
        verbose_name = "Module info"

    def __str__(self) -> str: return self.name
