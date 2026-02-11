from typing import Any

from django.db.models import QuerySet

import redis
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Post, PostStatus
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostSerializer

logger = logging.getLogger("blog")

CACHE_KEY_POSTS_LIST = "posts_list"
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
        cached_data = cache.get(CACHE_KEY_POSTS_LIST)
        if cached_data is not None:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            response = self.get_paginated_response(self.get_serializer(page, many=True).data)
            cache.set(CACHE_KEY_POSTS_LIST, response.data, CACHE_TTL_SECONDS)
            return response

        data = self.get_serializer(queryset, many=True).data
        cache.set(CACHE_KEY_POSTS_LIST, data, CACHE_TTL_SECONDS)
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
        cache.delete(CACHE_KEY_POSTS_LIST)

    def perform_update(self, serializer):
        logger.info("Post update by user: %s", self.request.user.id)
        serializer.save()
        cache.delete(CACHE_KEY_POSTS_LIST)

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