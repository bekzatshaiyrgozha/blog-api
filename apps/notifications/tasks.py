import json
import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger("notifications")
User = get_user_model()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(comment_id):
    """
    Handle new comment side effects:
    1. Create Notification for post author
    2. Publish WebSocket event to all subscribers
    
    Retries matter here because:
    - Database can be temporarily unavailable
    - Redis publish can fail
    - Channel layer can be slow
    
    With retries, we ensure notifications reach users eventually.
    """
    from .models import Notification
    from apps.blog.models import Comment
    import redis
    
    try:
        comment = Comment.objects.select_related("post", "author").get(id=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f"Comment {comment_id} not found")
        return
    
    # 1) Create notification for post author
    if comment.author != comment.post.author:
        notification, created = Notification.objects.get_or_create(
            recipient=comment.post.author,
            comment=comment,
        )
        if created:
            logger.info(f"Notification created for user {comment.post.author_id}")
    
    # 2) Publish WebSocket event to Channels group
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        group_name = f"post_comments_{comment.post.slug}"
        
        payload = {
            "comment_id": comment.id,
            "author": {
                "id": comment.author.id,
                "email": comment.author.email,
            },
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
        }
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "comment_created",
                "data": payload,
            },
        )
        logger.info(f"WebSocket event sent to group {group_name}")
    except Exception as e:
        logger.exception(f"Failed to publish WebSocket event: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def clear_expired_notifications():
    """
    Delete notifications older than 30 days.
    
    Retries matter for database operations.
    """
    from .models import Notification
    
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f"Deleted {deleted} expired notifications")