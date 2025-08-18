from collections import OrderedDict

from rest_framework import serializers

from .models import ContactGroup


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
