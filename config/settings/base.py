from __future__ import annotations

from email.utils import getaddresses
from pathlib import Path

import environ
from celery.schedules import crontab

PROJECT_NAME = "vivace-proxies-manager"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "proxies"


env = environ.Env()
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))


# GENERAL
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)
BASE_URL = env("BASE_URL", default="http://127.0.0.1:8000")
RELEASE_VERSION = env("RELEASE_VERSION", default="unknown")


# APPS
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "proxies.users",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "proxies.proxies",
]


# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
            ],
        },
    },
]


# EMAILS
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="proxies-manager@zeleny.dev")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)


# ADMIN
# ------------------------------------------------------------------------------
DJANGO_ADMIN_URL = "admin/"
ADMINS = getaddresses([env("ADMINS", default="Jan Zeleny <zelenja8@gmail.com>")])
MANAGERS = ADMINS


# INTERNATIONALIZATION
# ------------------------------------------------------------------------------
TIME_ZONE = "Europe/Prague"
LANGUAGE_CODE = "en"
USE_I18N = False
USE_TZ = True


# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL", default="postgres:///proxies-manager")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# FIXTURES
# ------------------------------------------------------------------------------
FIXTURE_DIRS = [BASE_DIR / "fixtures"]


# LOCALE
# ------------------------------------------------------------------------------
LOCALE_PATHS = [BASE_DIR / "locale"]


# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}


# URLS
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# AUTHENTICATION
# ------------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"


# PASSWORDS
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# SECURITY
# ------------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True


# STATIC & MEDIA
# ------------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# also need to set this way for easy_thumbnails
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
FILE_UPLOAD_PERMISSIONS = 0o664
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o775

if whitenoise_static_prefix := env("WHITENOISE_STATIC_PREFIX", default=None):
    WHITENOISE_STATIC_PREFIX = whitenoise_static_prefix

STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]


# DRF
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "proxies.users.authentication.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}


# CELERY
# ------------------------------------------------------------------------------
if USE_TZ:
    CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = env("BROKER_URL", default="pyamqp://localhost")
CELERY_TASK_DEFAULT_QUEUE = PROJECT_NAME
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_IGNORE_RESULT = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_CACHE_BACKEND = "default"
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_RESULT_BACKEND = f"{env('REDIS_URL', default='redis://localhost:6379')}/0"

# Disable beat by default. Test if everything works first then enable it.
if env.bool("CELERY_BEAT_ENABLED", default=True):
    CELERY_BEAT_SCHEDULE = {
        "check_all_proxies": {
            "task": "proxies.proxies.tasks.check_all_proxies",
            "schedule": crontab(minute="*/5"),
        },
        "update_proxies_from_services": {
            "task": "proxies.proxies.tasks.update_proxies_from_services",
            "schedule": crontab(minute="5", hour="4"),
        },
    }


# PROJECT SPECIFIC
# ------------------------------------------------------------------------------
PROXY_LOGIN = env("PROXY_LOGIN")
PROXY_PASSWORD = env("PROXY_PASSWORD")
PROXY_PORT = 3128


# DO PROXY DROPLETS
# ------------------------------------------------------------------------------
DO_LIMIT = 30
DO_TOKEN = env("DO_TOKEN")
DO_PROJECT_ID = env("DO_PROJECT_ID")
DO_PROXY_DROPLET_REGION = "fra1"
DO_PROXY_DROPLET_SIZE = "s-1vcpu-512mb-10gb"
DO_PROXY_DROPLET_IMAGE = "centos-stream-9-x64"


# HETZNER CONFIG
# ------------------------------------------------------------------------------
HETZNER_LIMIT = 5
HETZNER_TOKEN = env("HETZNER_TOKEN")
HETZNER_PROXY_SERVER_IMAGE = "centos-stream-9"
HETZNER_PROXY_SERVER_TYPE = "cx22"
HETZNER_PROXY_SERVER_LOCATION = "nbg1"
