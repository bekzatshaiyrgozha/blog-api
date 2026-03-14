from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_timezone(value: str):
    """
    Validate that `value` is a real IANA timezone identifier.
    Tries zoneinfo.available_timezones() first (Python 3.9+); falls back to pytz.
    Raises ValidationError with a translatable message on failure.
    """
    # Try zoneinfo (stdlib)
    try:
        from zoneinfo import available_timezones
        zones = available_timezones()
        if value in zones:
            return
    except Exception:
        zones = None

    # Fallback to pytz if zoneinfo not available or doesn't contain zones
    try:
        import pytz
        if value in pytz.all_timezones:
            return
    except Exception:
        # pytz not installed or other error
        pass

    raise ValidationError(_("Invalid timezone identifier."))