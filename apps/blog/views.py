import json
import logging
from typing import Any

from django.db.models import QuerySet

import redis
from django.core.cache import cache
from django_redis import get_redis_connection
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Post, PostStatus
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostSerializer
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
import httpx
import asyncio

logger = logging.getLogger("blog")

CACHE_KEY_POSTS_LIST_PREFIX = "posts_list"
CACHE_TTL_SECONDS = 60


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
        # Cache key is language- and page-aware so different languages get separate cached responses
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
        serializer.save(author=self.request.user)
        # Invalidate posts list cache for all languages and pages.
        try:
            conn = get_redis_connection("default")
            for key in conn.scan_iter(f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang=*"):
                conn.delete(key)
        except Exception:
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern(f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang=*")
            else:
                # best-effort fallback: delete known prefix keys if cached locally
                cache.delete(f"{CACHE_KEY_POSTS_LIST_PREFIX}")

    def perform_update(self, serializer):
        logger.info("Post update by user: %s", self.request.user.id)
        serializer.save()
        try:
            conn = get_redis_connection("default")
            for key in conn.scan_iter(f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang=*"):
                conn.delete(key)
        except Exception:
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern(f"{CACHE_KEY_POSTS_LIST_PREFIX}:lang=*")
            else:
                cache.delete(f"{CACHE_KEY_POSTS_LIST_PREFIX}")

    def perform_destroy(self, instance):
        logger.info("Post delete by user: %s", self.request.user.id)
        instance.delete()

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, slug=None):
        post = self.get_object()
        if request.method.lower() == "get":
            comments = post.comments.all()
            return Response(CommentSerializer(comments, many=True).data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        logger.info("Comment created by user: %s", request.user.id)

# Pub/Sub: publish event to Redis
        # Pub/Sub: publish event to Redis
        try:
            r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
            event_data = {
                "post_slug": post.slug,
                "author": request.user.email,
                "body": serializer.data.get("body"),
                }
            r.publish("comments", json.dumps(event_data))
        except Exception as e:
            logger.exception("Error publishing to Redis: %s", e)

        return Response(serializer.data, status=201)


@api_view(["GET"])
async def stats(request):
    """Async endpoint that fetches exchange rates and Almaty time concurrently.

    Returns blog counts from local DB and data from two external APIs.
    """
    # Async is used here because the view performs two independent network I/O operations
    # (external HTTP requests). Using asyncio.gather with httpx.AsyncClient allows both
    # requests to run concurrently so total latency approximates the slower call, not the sum.
    # local counts (synchronous ORM is fine here; it's fast)
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