from __future__ import annotations

from .base import *  # noqa: F403

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = "django-insecure-jafr+3z+xs!x4v3-b-y_vi4-&59_f%fbqme=)g4z06(py79h#y"  # noqa: S105
ALLOWED_HOSTS = ["*"]


# EMAILS
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# PASSWORDS
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = []


# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "vivace": {"()": "config.logging.VivaceFormatter"},
        "colorama": {"()": "config.logging.ColoramaFormatter"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "colorama",
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console"]},
    "loggers": {
        "django.db.backends": {"level": "INFO"},
    },
}
