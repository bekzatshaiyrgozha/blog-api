# Project modules
from settings.base import *


DEBUG = True
ALLOWED_HOSTS = []
INTERNAL_IPS = [
    "127.0.0.1",
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': config("BLOG_SQLITE_PATH", default=os.path.join(BASE_DIR, "db.sqlite3"), cast=str),
    },
}