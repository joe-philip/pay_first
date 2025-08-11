from collections import OrderedDict

from rest_framework import serializers

from .models import ContactGroup


class ContactGroupSerializer(serializers.ModelSerializer):
    def validate_parent_group(self, value):
        if value and value.owner != self.context['request'].user:
            raise serializers.ValidationError(
                "You do not have permission to add contacts to this group."
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
