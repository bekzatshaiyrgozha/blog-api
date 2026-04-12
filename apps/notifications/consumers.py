import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.blog.models import Post


User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]

        # 1) token из query string: ?token=...
        raw_qs = self.scope.get("query_string", b"").decode()
        token = parse_qs(raw_qs).get("token", [None])[0]
        if not token:
            await self.close(code=4001)
            return

        # 2) валидация JWT
        try:
            access = AccessToken(token)
            user_id = access.get("user_id")
            if not user_id:
                await self.close(code=4001)
                return
        except TokenError:
            await self.close(code=4001)
            return
        except Exception:
            await self.close(code=4001)
            return

        # 3) проверка пользователя
        user = await sync_to_async(User.objects.filter(id=user_id, is_active=True).first)()
        if not user:
            await self.close(code=4001)
            return

        # 4) проверка поста по slug
        post_exists = await sync_to_async(Post.objects.filter(slug=self.slug).exists)()
        if not post_exists:
            await self.close(code=4004)
            return

        # 5) group join
        self.group_name = f"post_comments_{self.slug}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def comment_created(self, event):
        # event["data"] ожидается в формате:
        # {comment_id, author:{id,email}, body, created_at}
        await self.send(text_data=json.dumps(event["data"], ensure_ascii=False))