import logging

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import RegisterSerializer
from django.template.loader import render_to_string
from django.utils import translation
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from .serializers import LanguageSerializer, TimezoneSerializer, UserSerializer

class UpdateLanguageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LanguageSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.language = serializer.validated_data["language"]
        request.user.save(update_fields=["language"])
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

class UpdateTimezoneView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TimezoneSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

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

        # Send welcome email in the user's chosen language
        
        # Dispatch welcome email task
        user_id = response.data.get("id")
        if user_id:
            from apps.users.tasks import send_welcome_email
            send_welcome_email.delay(user_id)

        return response