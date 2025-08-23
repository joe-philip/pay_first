from django.db.models import QuerySet
from collections import OrderedDict

from rest_framework import serializers

from .models import ContactGroup, Contacts


class ContactGroupSerializer(serializers.ModelSerializer):
    def validate_name(self, value):
        contact_groups = ContactGroup.objects.filter(
            name=value, owner=self.context["request"].user
        )
        if instance := getattr(self, 'instance', None):
            contact_groups = contact_groups.exclude(id=instance.id)
        if contact_groups.exists():
            raise serializers.ValidationError(
                "This contact group already exists"
            )
        return value

    def validate_parent_group(self, value):
        if value and value.owner != self.context['request'].user:
            raise serializers.ValidationError(
                "You do not have permission to add sub groups to this group."
            )
        if instance := getattr(self, "instance", None):
            if value == instance:
                raise serializers.ValidationError(
                    "Parent group cannot be the same instance"
                )
        return value

    class Meta:
        model = ContactGroup
        fields = '__all__'
        read_only_fields = ('owner',)

    def save(self, **kwargs):
        request = self.context.get('request')
        kwargs['owner'] = request.user
        return super().save(**kwargs)

    def to_representation(self, instance: ContactGroup) -> OrderedDict:
        data = super().to_representation(instance)
        subgroups = instance.subgroups.all()
        if subgroups.exists():
            data['subgroups'] = ContactGroupSerializer(
                subgroups, many=True
            ).data
        return data


class ContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacts
        fields = "__all__"
        read_only_fields = ("owner",)
        extra_kwargs = {
            "groups": {"allow_empty": True}
        }

    def validate_groups(self, value: QuerySet[ContactGroup]) -> QuerySet[ContactGroup]:
        invalid_groups = []
        for item in value:
            if item.owner != self.context["request"].user:
                invalid_groups.append(str(item))
        if invalid_groups:
            raise serializers.ValidationError(f"Invalid group names {', '.join(invalid_groups)}")
        return value

    def save(self, **kwargs):
        kwargs["owner"] = self.context["request"].user
        return super().save(**kwargs)
