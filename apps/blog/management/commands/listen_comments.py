import json

import redis
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Subscribe to Redis comments channel and print events"

    def handle(self, *args, **options):
        r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe("comments")

        self.stdout.write(self.style.SUCCESS("Listening to comments channel..."))

        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    self.stdout.write(
                        f"[{data.get('created_at')}] {data.get('author')} commented on {data.get('post_slug')}: {data.get('body')}"
                    )
                except json.JSONDecodeError:
                    self.stdout.write(f"Raw message: {message['data']}")