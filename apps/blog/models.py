from django.conf import settings
from django.db import models


class PostStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    SCHEDULED = "scheduled", "Scheduled"


class Category(models.Model):
    # Keep `name` as the English name for backward compatibility
    name = models.CharField(max_length=100, unique=True, verbose_name="Name (en)")
    name_ru = models.CharField(max_length=100, null=True, blank=True, verbose_name="Name (ru)")
    name_kz = models.CharField(max_length=100, null=True, blank=True, verbose_name="Name (kz)")
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(max_length=20, choices=PostStatus.choices, default=PostStatus.DRAFT)
    publish_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comment by {self.author_id} on {self.post_id}"