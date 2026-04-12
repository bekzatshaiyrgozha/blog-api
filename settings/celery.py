import os
from celery import Celery
from celery.schedules import crontab
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.env.local")

app = Celery("blog_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Broker и result backend на Redis (отдельная DB, отличная от cache и channel layer)
BLOG_CELERY_BROKER_URL = config(
    "BLOG_CELERY_BROKER_URL",
    default="redis://127.0.0.1:6379/1",
    cast=str,
)

app.conf.update(
    broker_url=BLOG_CELERY_BROKER_URL,
    result_backend=BLOG_CELERY_BROKER_URL,
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

# Beat schedule для периодических задач
app.conf.beat_schedule = {
    "publish-scheduled-posts": {
        "task": "apps.blog.tasks.publish_scheduled_posts",
        "schedule": crontab(minute="*"),  # каждую минуту
    },
    "clear-expired-notifications": {
        "task": "apps.notifications.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),  # 03:00 UTC
    },
    "generate-daily-stats": {
        "task": "apps.blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),  # 00:00 UTC
    },
}