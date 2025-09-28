from django.db.models import DateTimeField, Model


class MetaModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


DEFAULT_READ_ONLY_FIELDS = ("created_at", "updated_at")
