from __future__ import annotations

from django.apps import AppConfig


class ProxiesConfig(AppConfig):
    """AppConfig for proxies app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "proxies.proxies"

    def ready(self) -> None:
        """Import signals."""
        from . import signals  # noqa: F401
