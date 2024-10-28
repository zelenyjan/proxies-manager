from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.db import transaction
from django.http import HttpRequest

from proxies.proxies.models import Client, Proxy
from proxies.proxies.tasks import create_server


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    """Admin for Proxy."""

    list_display = ["name", "active", "server_id", "provider", "ipaddress", "reported"]
    list_filter = ["active", "provider", "reported"]

    def get_readonly_fields(self, request: HttpRequest, obj: Proxy | None = None) -> list[str]:
        """Return readonly fields."""
        readonly_fields = [
            "server_id",
            "ipaddress",
            "active",
            "create_request_at",
            "create_response",
            "last_check_at",
            "last_check_response",
        ]
        if obj is not None:
            readonly_fields.insert(0, "name")
        return readonly_fields

    def save_model(self, request, obj, form, change):
        """Save model."""
        if (
            obj.provider == Proxy.ProviderChoices.DIGITALOCEAN
            and Proxy.objects.filter(provider=obj.provider).count() >= settings.DO_LIMIT
        ):
            self.message_user(
                request,
                f"You can't create more then {settings.DO_LIMIT} proxies for Digitalocean provider.",
                level="ERROR",
            )
            return

        if (
            obj.provider == Proxy.ProviderChoices.HETZNER
            and Proxy.objects.filter(provider=obj.provider).count() >= settings.HETZNER_LIMIT
        ):
            self.message_user(
                request,
                f"You can't create more then {settings.HETZNER_LIMIT} proxies for Hetzner provider.",
                level="ERROR",
            )
            return

        super().save_model(request, obj, form, change)
        if not obj.create_request_at:
            transaction.on_commit(lambda: create_server.delay(obj.pk))


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin for Client."""

    list_display = ["name"]
    search_fields = ["name"]
