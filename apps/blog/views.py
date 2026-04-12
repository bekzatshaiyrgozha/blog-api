import asyncio
import json
import logging

import httpx
import redis
import redis.asyncio as aioredis
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Post, PostStatus
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostSerializer

logger = logging.getLogger("blog")

CACHE_KEY_POSTS_LIST_PREFIX = "posts_list"
CACHE_TTL_SECONDS = 60
POST_PUBLISHED_CHANNEL = "posts_published"


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Post]:
        if self.action in ["list", "retrieve"]:
            return Post.objects.filter(status=PostStatus.PUBLISHED)
        return Post.objects.all()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "comments":
            if self.request.method.lower() == "get":
                return [AllowAny()]
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def list(self, request, *args, **kwargs):
        lang = getattr(request, "LANGUAGE_CODE", "en")
        page = request.query_params.get("page", "1")
        cache_key = f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang={lang}:page={page}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(self.get_serializer(page, many=True).data)
            cache.set(cache_key, response.data, CACHE_TTL_SECONDS)
            return response

        data = self.get_serializer(queryset, many=True).data
        cache.set(cache_key, data, CACHE_TTL_SECONDS)
        return Response(data)

    @method_decorator(ratelimit(key="user", rate="20/m", method="POST", block=False))
    def create(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return Response(
                {"detail": "Too many requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        logger.info("Post creation by user: %s", self.request.user.id)
        post = serializer.save(author=self.request.user)

        from apps.blog.tasks import invalidate_posts_cache

        invalidate_posts_cache.delay()

        if post.status == PostStatus.PUBLISHED:
            publish_post_published_event(post)

    def perform_update(self, serializer):
        logger.info("Post update by user: %s", self.request.user.id)
        old_status = serializer.instance.status
        post = serializer.save()

        from apps.blog.tasks import invalidate_posts_cache

        invalidate_posts_cache.delay()

        if post.status == PostStatus.PUBLISHED and old_status != PostStatus.PUBLISHED:
            publish_post_published_event(post)

    def perform_destroy(self, instance):
        logger.info("Post delete by user: %s", self.request.user.id)
        instance.delete()

        from apps.blog.tasks import invalidate_posts_cache

        invalidate_posts_cache.delay()

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, slug=None):
        post = self.get_object()
        if request.method.lower() == "get":
            comments = post.comments.all()
            return Response(CommentSerializer(comments, many=True).data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, author=request.user)
        logger.info("Comment created by user: %s", request.user.id)

        from apps.notifications.tasks import process_new_comment

        process_new_comment.delay(comment.id)

        return Response(CommentSerializer(comment).data, status=201)


def publish_post_published_event(post):
    payload = {
        "post_id": post.id,
        "title": post.title,
        "slug": post.slug,
        "author": {
            "id": post.author_id,
            "email": post.author.email,
        },
        "published_at": post.updated_at.isoformat() if post.updated_at else None,
    }
    try:
        r = redis.Redis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
        r.publish(POST_PUBLISHED_CHANNEL, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.exception("Failed to publish SSE event: %s", e)


async def _sse_post_stream():
    client = aioredis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(POST_PUBLISHED_CHANNEL)

    try:
        yield ": connected\n\n"
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message.get("data")
            yield f"data: {data}\n\n"
    finally:
        await pubsub.unsubscribe(POST_PUBLISHED_CHANNEL)
        await pubsub.close()
        await client.close()


@api_view(["GET"])
@permission_classes([AllowAny])
async def posts_stream(request):
    # SSE is a good fit for one-way server->client updates (simple, lightweight).
    # For bidirectional communication (client<->server) or complex real-time features,
    # WebSockets are a better choice.
    response = StreamingHttpResponse(
        streaming_content=_sse_post_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
async def stats(request):
    total_posts = Post.objects.count()
    total_comments = Comment.objects.count()
    from django.contrib.auth import get_user_model

    User = get_user_model()
    total_users = User.objects.count()

    async with httpx.AsyncClient(timeout=10.0) as client:
        task_rates = client.get("https://open.er-api.com/v6/latest/USD")
        task_time = client.get("https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty")
        resp_rates, resp_time = await asyncio.gather(task_rates, task_time)

    rates_json = resp_rates.json() if resp_rates.status_code == 200 else {}
    time_json = resp_time.json() if resp_time.status_code == 200 else {}

    rates = rates_json.get("rates", {})
    result = {
        "blog": {"total_posts": total_posts, "total_comments": total_comments, "total_users": total_users},
        "exchange_rates": {"KZT": rates.get("KZT"), "RUB": rates.get("RUB"), "EUR": rates.get("EUR")},
        "current_time": time_json.get("dateTime"),
    }
    return Response(result)