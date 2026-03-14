import asyncio
import json
import asyncio
from django.core.management.base import BaseCommand

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None


class Command(BaseCommand):
    help = "Async subscriber to Redis comments channel that prints JSON events"

    async def _listen(self):
        if aioredis is None:
            self.stderr.write("Async redis client not available. Install redis>=4.2")
            return

        r = aioredis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe("comments")

        self.stdout.write(self.style.SUCCESS("Listening to comments channel (async)..."))
        # This command is async to avoid blocking the main thread while waiting for messages from Redis.
        # Using an async Redis client and asyncio keeps the event loop free to handle many subscriptions concurrently.

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    self.stdout.write(
                        f"[{data.get('created_at')}] {data.get('author')} commented on {data.get('post_slug')}: {data.get('body')}"
                    )
                except json.JSONDecodeError:
                    self.stdout.write(f"Raw message: {message['data']}")

    def handle(self, *args, **options):
        # Run the async listener in the event loop
        try:
            asyncio.run(self._listen())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Listener stopped"))