from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.blog.models import Category, Tag, Post, Comment, PostStatus


class Command(BaseCommand):
    help = "Seed database with sample users, categories, tags, posts and comments"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(email="admin@example.com").exists():
            User.objects.create_superuser(email="admin@example.com", password="adminpass", first_name="Admin", last_name="User")

        # Categories
        cats = [
            {"name": "Technology", "name_ru": "Технологии", "name_kz": "Технологиялар", "slug": "technology"},
            {"name": "Life", "name_ru": "Жизнь", "name_kz": "Өмір", "slug": "life"},
        ]
        for c in cats:
            Category.objects.update_or_create(slug=c["slug"], defaults=c)

        # Tags
        tags = ["django", "python", "tutorial"]
        tag_objs = []
        for t in tags:
            tag, _ = Tag.objects.get_or_create(name=t, slug=t)
            tag_objs.append(tag)

        # Users
        if not User.objects.filter(email="user1@example.com").exists():
            u1 = User.objects.create_user(email="user1@example.com", password="pass1234", first_name="U1", last_name="User")
        else:
            u1 = User.objects.get(email="user1@example.com")

        # Posts
        if not Post.objects.filter(slug="welcome-post").exists():
            post = Post.objects.create(author=u1, title="Welcome", slug="welcome-post", body="Hello world", status=PostStatus.PUBLISHED, category=Category.objects.first())
            post.tags.set(tag_objs[:2])

        # Comments
        post = Post.objects.filter(slug="welcome-post").first()
        if post and not post.comments.exists():
            Comment.objects.create(post=post, author=u1, body="Nice post!")

        self.stdout.write(self.style.SUCCESS("Seed data installed or already present."))
