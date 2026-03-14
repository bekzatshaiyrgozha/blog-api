from rest_framework import serializers
from .models import Category, Tag, Post, Comment
from django.utils import timezone as dj_timezone
from django.utils import formats


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "name_en", "name_ru", "name_kz")

    def get_name(self, obj):
        # Determine active language from request context
        request = self.context.get("request")
        lang = None
        if request is not None:
            lang = getattr(request, "LANGUAGE_CODE", None)
        # map language to field
        if lang == "ru" and getattr(obj, "name_ru", None):
            return obj.name_ru
        if lang == "kz" and getattr(obj, "name_kz", None):
            return obj.name_kz
        # fallback to English name
        return obj.name


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class PostSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "slug",
            "body",
            "category",
            "tags",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("author", "created_at", "updated_at")

    def _format_dt(self, dt):
        if dt is None:
            return None
        # convert to active timezone (middleware activates user's timezone or UTC)
        local_dt = dj_timezone.localtime(dt)
        # format according to active locale
        return formats.date_format(local_dt, format="DATETIME_FORMAT")

    def get_created_at(self, obj):
        return self._format_dt(obj.created_at)

    def get_updated_at(self, obj):
        return self._format_dt(obj.updated_at)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "post", "author", "body", "created_at")
        read_only_fields = ("author", "created_at")