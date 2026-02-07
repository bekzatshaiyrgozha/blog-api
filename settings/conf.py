# Project modules
from decouple import config


ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)

ENV_ID = config("BLOG_ENV_ID",default="local",cast = str)

SECRET_KEY = 'django-insecure-b@wp(sggy#_@61*7gxq5-yxu)y54&t1w#f*f2dbkq(f0kc=1qo'
