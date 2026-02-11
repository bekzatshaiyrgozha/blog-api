# Project modules
from decouple import config


ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)

ENV_ID = config("BLOG_ENV_ID",default="local",cast = str)

SECRET_KEY = config("BLOG_SECRET_KEY", cast=str)
DEBUG = config("BLOG_DEBUG", default=False, cast=bool)
