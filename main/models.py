from django.db import models

# Create your models here.


class AppSettings(models.Model):
    app_name = models.CharField(max_length=50)
    version = models.CharField(max_length=10)
    tag = models.CharField(max_length=50, help_text="Commit hash on tag")
    change_log = models.TextField()
    terms_and_conditions = models.TextField()

    class Meta:
        db_table = "app_settings"
        verbose_name = "App setting"
