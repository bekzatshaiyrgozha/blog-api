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
        try:
            user_email = response.data.get("email")
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(email=user_email).first()
            if user:
                user_lang = getattr(user, "language", settings.LANGUAGE_CODE)
                # render templates in user's language regardless of current request language
                with translation.override(user_lang):
                    subject = render_to_string("emails/welcome/subject.txt", {"user": user}).strip()
                    body = render_to_string("emails/welcome/body.txt", {"user": user})
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception:
            logger.exception("Failed to send welcome email")

        return response