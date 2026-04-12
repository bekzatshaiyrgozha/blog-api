from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source="comment.id", read_only=True)
    comment_body = serializers.CharField(source="comment.body", read_only=True)
    post_slug = serializers.CharField(source="comment.post.slug", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "comment_id",
            "comment_body",
            "post_slug",
            "is_read",
            "created_at",
        )