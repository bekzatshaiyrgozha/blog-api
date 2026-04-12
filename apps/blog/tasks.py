import logging
from celery import shared_task
from django.core.cache import cache
from django_redis import get_redis_connection

logger = logging.getLogger("blog")

CACHE_KEY_POSTS_LIST_PREFIX = "posts_list"


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_posts_cache():
    """
    Invalidate all cached posts lists.
    
    Retries matter here because Redis connection can fail temporarily.
    With retries, we ensure cache is eventually cleared even if Redis
    was briefly unavailable.
    """
    try:
        conn = get_redis_connection("default")
        for key in conn.scan_iter(f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang=*"):
            conn.delete(key)
        logger.info("Posts cache invalidated")
    except Exception as e:
        logger.exception(f"Failed to invalidate cache: {e}")
        raise


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def publish_scheduled_posts():
    """
    Find posts with status=scheduled and publish_at <= now(), publish them.
    
    Retries are important because:
    - Database connection can fail
    - Redis publish can fail
    With retries, we ensure scheduled posts are eventually published.
    """
    from django.utils import timezone
    from .models import Post, PostStatus
    from apps.blog.views import publish_post_published_event
    
    now = timezone.now()
    posts = Post.objects.filter(
        status=PostStatus.SCHEDULED,
        publish_at__lte=now,
    )
    
    updated = 0
    for post in posts:
        post.status = PostStatus.PUBLISHED
        post.save(update_fields=["status"])
        publish_post_published_event(post)
        updated += 1
    
    logger.info(f"Published {updated} scheduled posts")


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_daily_stats():
    """
    Generate and log daily statistics.
    
    Retries matter for database queries that might temporarily fail.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    from .models import Post, Comment, PostStatus
    
    User = get_user_model()
    
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    
    new_posts = Post.objects.filter(created_at__gte=yesterday).count()
    new_comments = Comment.objects.filter(created_at__gte=yesterday).count()
    new_users = User.objects.filter(date_joined__gte=yesterday).count()
    
    logger.info(
        f"Daily stats: {new_posts} new posts, "
        f"{new_comments} new comments, {new_users} new users"
    )