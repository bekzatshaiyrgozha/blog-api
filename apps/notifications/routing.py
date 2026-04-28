from django.urls import path
from .consumers import CommentConsumer

websocket_urlpatterns = [
    path("ws/posts/<slug:slug>/comments/", CommentConsumer.as_asgi()),
    # debug endpoint for HW4 verification (returns simple echo)
    path("ws/", DebugConsumer.as_asgi()),
]