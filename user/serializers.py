from collections import OrderedDict

from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.request import Request

from .models import (ContactGroup, Contacts, PaymentMethods, PaymentSources,
                     Repayments, Transactions)


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
            raise serializers.ValidationError(
                f"Invalid group names {', '.join(invalid_groups)}")
        return value

    def save(self, **kwargs):
        kwargs["owner"] = self.context["request"].user
        return super().save(**kwargs)


class TransactionsSerializer(serializers.ModelSerializer):
    class RepaymentsSerializer(serializers.ModelSerializer):
        class Meta:
            model = Repayments
            exclude = ("transaction",)
    repayments = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()

    def validate_payment_method(self, value: PaymentMethods):
        if not value:
            default_payment_method = PaymentMethods.objects.filter(
                owner=self.context["request"].user, is_default=True
            )
            if default_payment_method.exists():
                return default_payment_method.first()
            return PaymentMethods.objects.filter(is_common=True).first()
        return value

    def get_repayments(self, instance: Transactions):
        return self.RepaymentsSerializer(instance.repayments.all(), many=True).data

    def get_pending_amount(self, instance: Transactions) -> float:
        return instance.pending_amount

    class Meta:
        model = Transactions
        fields = '__all__'
        extra_kwargs = {
            "payment_method": {"allow_null": True}
        }


class RepaymentsSerializer(serializers.ModelSerializer):
    def validate_payment_method(self, value: PaymentMethods):
        if not value:
            default_payment_method = PaymentMethods.objects.filter(
                owner=self.context["request"].user, is_default=True
            )
            if default_payment_method.exists():
                return default_payment_method.first()
            return PaymentMethods.objects.filter(is_common=True).first()
        return value

    class Meta:
        model = Repayments
        fields = '__all__'
        extra_kwargs = {"payment_method": {"allow_null": True}}


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethods
        fields = "__all__"
        read_only_fields = ("owner", "is_common")
        extra_kwargs = {"is_default": {"required": True, "allow_null": True}}

    def validate_label(self, value: str) -> str:
        queryset: QuerySet = self.context["view"].get_queryset()
        queryset = queryset.filter(owner=self.context["request"].user)
        if instance := getattr(self, "instance", None):
            queryset = queryset.exclude(id=instance.id)
        if queryset.filter(label=value).exists():
            raise serializers.ValidationError(
                "Instance with this name already exists"
            )
        return value

    def validate_is_default(self, value: bool) -> bool:
        queryset: QuerySet = self.context["view"].get_queryset()
        payment_methods = queryset.filter(
            owner=self.context["request"].user
        )
        if not payment_methods.exists():
            return True  # Returns True if user has no other payment_methods
        if instance := getattr(self, "instance", None):
            payment_methods = payment_methods.exclude(id=instance.id)
        if value:
            # Updates all other payment methods default key to False if the current payment method is True
            payment_methods.update(is_default=False)
        else:
            if not payment_methods.filter(is_default=True).exists():
                raise serializers.ValidationError(
                    "Atleast one payment method should be set to default payment method"
                )
        return value

    def save(self, **kwargs):
        request: Request = self.context["request"]
        kwargs["owner"] = request.user
        return super().save(**kwargs)


class PaymentSourcesSerializer(serializers.ModelSerializer):
    def validate_label(self, value: str) -> str:
        payment_sources = PaymentSources.objects.filter(
            label=value,
            owner=self.context["request"].user
        )
        if instance := getattr(self, "instance", None):
            payment_sources = payment_sources.exclude(id=instance.id)
        if payment_sources.exists():
            raise serializers.ValidationError("Payment source already exist")
        return value

    class Meta:
        model = PaymentSources
        fields = "__all__"
        read_only_fields = ("owner",)

    def save(self, **kwargs):
        kwargs["owner"] = self.context["request"].user
        return super().save(**kwargs)
