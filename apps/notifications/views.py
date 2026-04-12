from django.db.models import QuerySet
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self) -> QuerySet[Notification]:
        return (
            Notification.objects
            .filter(recipient=self.request.user)
            .select_related("comment", "comment__post")
            .order_by("-created_at")
        )


class NotificationCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Polling trade-off:
        # Polling is simple to implement and reliable for small/medium traffic,
        # but it introduces latency (depends on poll interval) and extra repeated
        # requests to the server. It is acceptable for non-critical "badge count"
        # updates. For truly real-time UX or high-frequency updates, prefer
        # WebSockets (bi-directional) or SSE (server -> client stream).
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)