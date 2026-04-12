# Project modules
from settings.base import *


DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': config("BLOG_SQLITE_PATH", default=os.path.join(BASE_DIR, "db.sqlite3"), cast=str),
    },
}