import os

from settings.conf import * 
from django.utils.translation import gettext_lazy as _



'''
Path configuration
'''
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATIONS = 'settings.asgi.applications'


LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('ru', _('Russian')),
    ('kz', _('Kazakh')),
]

SUPPORTED_LANGUAGES = [code for code, _ in LANGUAGES]
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

'''
Apps
'''

DJANGO_AND_THIRD_PARTY_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
]

PROJECT_APPS = [
    "apps.users",
    "apps.blog",
    "apps.core",
    
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

'''
MIDDLEWARE  || TEMPLATES || VALIDATORS
'''

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.core.middleware.UserLanguageTimezoneMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


'''
INSTALIZATION
'''

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

'''
STATIC || MEDIA
'''

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": "verbose",
            "filename": os.path.join(BASE_DIR, "logs", "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
        },
        "debug_requests": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": os.path.join(BASE_DIR, "logs", "debug_requests.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "filters": ["require_debug_true"],
        },
    },
    "loggers": {
        "users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "blog": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file", "debug_requests"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}