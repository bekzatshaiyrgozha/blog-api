from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import User
from .validators import validate_timezone
from django.conf import settings



User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password", "password_confirm", "tokens")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            from django.utils.translation import gettext_lazy as _
            raise serializers.ValidationError({"password_confirm": _("Passwords do not match")})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "language", "timezone", "avatar", "date_joined"]
        read_only_fields = ["id", "email", "date_joined"]

class LanguageSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=[(c, c) for c in getattr(settings, "SUPPORTED_LANGUAGES", ["en"])])

class TimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=64)

    def validate_timezone(self, value):
        validate_timezone(value)
        return value