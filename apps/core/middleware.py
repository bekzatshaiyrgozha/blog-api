from django.utils import translation, timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class UserLanguageTimezoneMiddleware(MiddlewareMixin):
    """
    Resolves language in this priority:
    1) authenticated user's `language` field
    2) ?lang= query param
    3) Accept-Language header
    4) settings.LANGUAGE_CODE (default)

    Also activates user's timezone (or UTC for anonymous).
    """
    def process_request(self, request):
        # 1. User preference
        user_lang = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            user_lang = getattr(request.user, "language", None)
        # 2. Query param
        qlang = request.GET.get("lang")
        # 3. Accept-Language header
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE")
        # Determine language
        lang = user_lang or qlang or (accept.split(",")[0] if accept else None) or settings.LANGUAGE_CODE
        # Normalize to supported language codes if necessary
        if hasattr(settings, "SUPPORTED_LANGUAGES"):
            supported = settings.SUPPORTED_LANGUAGES
            if lang not in supported:
                lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = translation.get_language()

        # Timezone activation
        tz = "UTC"
        if getattr(request, "user", None) and request.user.is_authenticated:
            tz = getattr(request.user, "timezone", "UTC") or "UTC"
        try:
            timezone.activate(tz)
        except Exception:
            timezone.deactivate()