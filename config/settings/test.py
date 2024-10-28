from __future__ import annotations

from .base import *  # noqa: F403

# GENERAL
# ------------------------------------------------------------------------------
SECRET_KEY = "django-insecure-jafr+3z+xs!x4v3-b-y_vi4-&59_f%fbqme=)g4z06(py79h#y"  # noqa: S105


# TESTS
# ------------------------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"


# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# PASSWORDS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
