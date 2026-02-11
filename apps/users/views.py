import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import RegisterSerializer

logger = logging.getLogger("users")


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=False), name="create")
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs) -> Response:
        if getattr(request, "limited", False):
            return Response(
                {"detail": "Too many requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        logger.info("Registration attempt for email: %s", request.data.get("email"))
        response = super().create(request, *args, **kwargs)
        logger.info("User registered: %s", response.data.get("email"))
        return response