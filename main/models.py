from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Now

from main.choices import OTPTypeChoices
from main.exceptions import OTPAlreadyExistsException
from main.managers import OTPManager
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
    privacy_policy = models.TextField()

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


class OTP(models.Model):
    otp = models.CharField(max_length=8)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    otp_type = models.PositiveSmallIntegerField(choices=OTPTypeChoices.choices)
    validity = models.DateTimeField()

    objects: OTPManager = OTPManager()

    class Meta:
        db_table = "otp"
        verbose_name = "OTP"

    @property
    def is_valid(self) -> bool:
        return self.objects.filter_valid_otps(
            otp=self.otp,
            user=self.user,
            otp_type=self.otp_type
        ).exists()

    def __str__(self) -> str:
        return self.user.first_name

    def save(self, *args, **kwargs):
        existing_otp = OTP.objects.filter(otp=self.otp, validity__gt=Now())
        if existing_otp.exists():
            raise OTPAlreadyExistsException()
        return super().save(*args, **kwargs)
