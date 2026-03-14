from django.contrib import admin
from django.urls import path, include
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.routers import DefaultRouter
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.views import RegisterViewSet
from apps.blog.views import PostViewSet
from apps.blog.views import stats as stats_view
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
except Exception:
    SpectacularAPIView = SpectacularRedocView = SpectacularSwaggerView = None

router = DefaultRouter()
router.register("auth/register", RegisterViewSet, basename="register")
router.register("posts", PostViewSet, basename="posts")

class TokenObtainPairRateLimitedView(TokenObtainPairView):
    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=False))
    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return Response({"detail": "Too many requests. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return super().post(request, *args, **kwargs)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # OpenAPI schema and docs
    # OpenAPI schema and docs (conditionally available if drf-spectacular is installed)
    *(
        [
            path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
            path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
        ]
        if SpectacularAPIView
        else []
    ),
    path("api/auth/token/", TokenObtainPairRateLimitedView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/stats/", stats_view, name="api-stats"),
]