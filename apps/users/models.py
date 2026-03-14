from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .managers import UserManager




class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self) -> str:
        return self.email
    
    language = models.CharField(
        max_length=5,
        choices=[(c, c) for c in getattr(settings, "SUPPORTED_LANGUAGES", ["en"])],
        default="en",
        verbose_name=_("Language"),
        help_text=_("Preferred language for the user interface"),
    )
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        verbose_name=_("Timezone"),
        help_text=_("Preferred timezone for the user"),
    )