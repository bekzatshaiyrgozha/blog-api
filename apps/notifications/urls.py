from django.urls import path
from .views import NotificationListView, NotificationCountView, MarkAllReadView


urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/count/", NotificationCountView.as_view(), name="notifications-count"),
    path("notifications/read/", MarkAllReadView.as_view(), name="notifications-read"),
]