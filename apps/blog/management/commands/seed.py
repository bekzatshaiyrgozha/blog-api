from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.blog.models import Category, Tag, Post, Comment, PostStatus


class Command(BaseCommand):
    help = "Seed database with sample users, categories, tags, posts and comments"

    def handle(self, *args, **options):
        User = get_user_model()

        # Superuser
        if not User.objects.filter(email="admin@example.com").exists():
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass",
                first_name="Admin",
                last_name="User",
            )

        # Categories
        cats = [
            {"name": "Technology", "name_ru": "Технологии", "name_kz": "Технологиялар", "slug": "technology"},
            {"name": "Life", "name_ru": "Жизнь", "name_kz": "Өмір", "slug": "life"},
        ]
        for c in cats:
            Category.objects.update_or_create(slug=c["slug"], defaults=c)

        # Tags
        tag_names = ["django", "python", "tutorial"]
        tag_objs = []
        for t in tag_names:
            tag, _ = Tag.objects.get_or_create(name=t, slug=t)
            tag_objs.append(tag)

        # User
        user, _ = User.objects.get_or_create(
            email="user1@example.com",
            defaults={
                "first_name": "U1",
                "last_name": "User",
            },
        )
        if not user.check_password("pass1234"):
            user.set_password("pass1234")
            user.save(update_fields=["password"])

        # Post
        post, _ = Post.objects.get_or_create(
            slug="welcome-post",
            defaults={
                "author": user,
                "title": "Welcome",
                "body": "Hello world",
                "status": PostStatus.PUBLISHED,
                "category": Category.objects.first(),
            },
        )
        post.tags.set(tag_objs[:2])

        # Comment
        if not post.comments.exists():
            Comment.objects.create(post=post, author=user, body="Nice post!")

        self.stdout.write(self.style.SUCCESS("Seed data installed or already present."))