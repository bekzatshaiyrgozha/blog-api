import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation

logger = logging.getLogger("users")
User = get_user_model()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_welcome_email(user_id):
    """
    Send welcome email to new user.
    
    Retries are important here because email delivery can fail due to:
    - Network issues (SMTP timeout, DNS failure)
    - Temporary mail server unavailability
    - Rate limiting from email provider
    
    With autoretry, the task will retry after exponential backoff
    (2^retry_count seconds) up to 3 times before giving up.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for welcome email")
        return

    user_lang = getattr(user, "language", settings.LANGUAGE_CODE)
    
    try:
        with translation.override(user_lang):
            subject = render_to_string("emails/welcome/subject.txt", {"user": user}).strip()
            body = render_to_string("emails/welcome/body.txt", {"user": user})
        
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.exception(f"Failed to send welcome email to {user.email}: {e}")
        raise