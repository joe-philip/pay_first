from django.contrib.auth import authenticate, get_user_model
from django.db.models.functions import Now
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import AuthenticationFailed

from main.choices import OTPTypeChoices
from main.error_codes import EMAIL_ALREADY_VERIFIED, EXPIRED_OTP, INVALID_OTP
from main.models import OTP, AppSettings, ModuleInfo
from main.models import User as UserModel

from .validators import is_email_format, user_exists, validate_password

User = get_user_model()


class SignupAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name',
            'username', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True}
        }

    def validate_username(self, value: str) -> str:
        """
        Validates the provided username by ensuring it is in email format and not already taken.

        Args:
            value (str): The username to validate.

        Returns:
            str: The validated and normalized (lowercase) username.

        Raises:
            serializers.ValidationError: If the username is not in a valid email format or already exists.
        """
        value = value.lower()
        if not is_email_format(value):
            raise serializers.ValidationError('Invalid email format')
        if user_exists(username=value):
            raise serializers.ValidationError('User already exists')
        return value

    def validate_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def save(self, **kwargs):
        user = super().save(**kwargs)
        user.set_password(self.validated_data.get('password'))
        user.save()
        return user


class LoginSerializer(AuthTokenSerializer):
    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            return value
        raise serializers.ValidationError('User does not exist')

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username, password=password
            )
            if not user:
                raise AuthenticationFailed(
                    'Invalid credentials', code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True
    )

    def validate_password(self, value: str) -> str:
        user: UserModel = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect old password')
        return value

    def validate_new_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def validate(self, attrs):
        if attrs.get('password') == attrs.get('new_password'):
            raise serializers.ValidationError(
                {
                    "new_password": ['New password cannot be the same as the old password']
                }
            )
        return attrs

    class Meta:
        model = User
        fields = ('password', 'new_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self, **kwargs):
        user: UserModel = self.context['request'].user
        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class MetaAPISerializer(serializers.Serializer):
    class ModuleInfoSerializer(serializers.ModelSerializer):
        class Meta:
            model = ModuleInfo
            depth = 1
            exclude = ("created_at", "updated_at")

    class AppSettingsSerializer(serializers.ModelSerializer):
        class Meta:
            model = AppSettings
            exclude = ("created_at", "updated_at")
    modules = ModuleInfoSerializer(many=True)
    app_settings = AppSettingsSerializer()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        value = value.lower()
        if not is_email_format(value):
            raise serializers.ValidationError('Invalid email format')
        if not user_exists(username=value):
            raise serializers.ValidationError('User does not exist')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )
    otp = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        validation_errors = validate_password(value)
        if not validation_errors:
            return value
        raise serializers.ValidationError(validation_errors)

    def validate(self, attrs):
        otp = OTP.objects.filter(
            user__username=attrs["email"].username,
            otp=attrs["otp"]
        )
        if not otp.exists():
            raise serializers.ValidationError(
                {"otp": ["Invalid OTP"]},
                code=INVALID_OTP
            )
        otp = otp.filter(
            validity__gt=Now()
        )
        if not otp.exists():
            raise serializers.ValidationError(
                {"otp": ["OTP has expired"]},
                code=EXPIRED_OTP
            )
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["email"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        OTP.objects.filter(
            user=user, otp_type=OTPTypeChoices.FORGOT_PASSWORD.value
        ).delete()


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )
    otp = serializers.CharField()

    def validate(self, attrs):
        user = attrs["email"]
        otp = OTP.objects.filter(
            user__username=user.username,
            otp_type=OTPTypeChoices.EMAIL_VERIFICATION.value,
            otp=attrs["otp"]
        )
        if not otp.exists():
            raise serializers.ValidationError(
                {"otp": ["Invalid OTP"]},
                code=INVALID_OTP
            )
        valid_otps = otp.filter_valid_otps()
        if not valid_otps.exists():
            raise serializers.ValidationError(
                {"otp": ["OTP has expired"]},
                code=EXPIRED_OTP
            )
        if user.email_verified:
            raise serializers.ValidationError(
                {"email": ["Email already verified"]},
                code=EMAIL_ALREADY_VERIFIED
            )
        return super().validate(attrs)

    def save(self, **kwargs) -> UserModel:
        user = self.validated_data["email"]
        user.email_verified = True
        user.save()
        OTP.objects.filter(
            user=user, otp_type=OTPTypeChoices.EMAIL_VERIFICATION.value
        ).delete()
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    def validate_email(self, value):
        if value.email_verified:
            raise serializers.ValidationError(
                'Email already verified', code=EMAIL_ALREADY_VERIFIED)
        return value
