from django.contrib import admin

from .models import AppSettings, ModuleInfo

# Register your models here.

admin.site.register(AppSettings)
admin.site.register(ModuleInfo)
