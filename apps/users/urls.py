from django.urls import path
from .views import UpdateLanguageView, UpdateTimezoneView

urlpatterns = [
    path("auth/language/", UpdateLanguageView.as_view(), name="update-language"),
    path("auth/timezone/", UpdateTimezoneView.as_view(), name="update-timezone"),
]