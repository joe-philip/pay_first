import logging

from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.utils import clear_meta_api_cache
from root.utils.utils import clear_cache

from .models import AppSettings, ModuleInfo


@receiver(post_save, sender=AppSettings)
def appsettings_post_save(sender, instance: AppSettings, created: bool, **kwargs):
    clear_meta_api_cache()


@receiver(post_save, sender=ModuleInfo)
def module_info_post_save(sender, instance: ModuleInfo, created: bool, **kwargs):
    clear_meta_api_cache()
