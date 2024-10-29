from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

import httpx
from model_utils.models import UUIDModel

from proxies.proxies.utils import get_random_string

if TYPE_CHECKING:
    from proxies.proxies.services.base import BaseService

logger = logging.getLogger(__name__)


def default_proxy_name() -> str:
    """
    Generate random name for proxy(droplet). Check if name is unique(not used before).

    :return: random name for proxy(droplet)
    """
    while True:
        name = get_random_string(8, upper_case=False, digits=False, can_start_with_digit=False)
        try:
            Proxy.objects.get(name=name)
        except Proxy.DoesNotExist:
            return name


class Proxy(UUIDModel):
    """Proxy server(droplet) on DigitalOcean."""

    class ProviderChoices(models.TextChoices):
        DIGITALOCEAN = "digitalocean", "DigitalOcean"
        HETZNER = "hetzner", "Hetzner"

    name = models.CharField(max_length=64, unique=True, default=default_proxy_name)
    alias = models.CharField(max_length=64, default="", blank=True)
    provider = models.CharField(max_length=32, choices=ProviderChoices, default=ProviderChoices.DIGITALOCEAN)
    server_id = models.PositiveIntegerField(null=True)
    ipaddress = models.GenericIPAddressField(protocol="ipv4", null=True)
    active = models.BooleanField(default=False)
    create_request_at = models.DateTimeField(null=True)
    create_response = models.JSONField(null=True)
    last_check_at = models.DateTimeField(null=True)
    last_check_response = models.JSONField(null=True)
    reported = models.BooleanField(default=False, editable=False)
    is_removed = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "proxy"
        verbose_name_plural = "proxies"

    def __str__(self) -> str:
        """Return proxy name."""
        return f"{self.name} ({self.alias})" or self.name

    def get_service(self) -> BaseService:
        """Get service for proxy provider."""
        if self.provider == self.ProviderChoices.DIGITALOCEAN:
            from proxies.proxies.services.digitalocean import DigitalOceanService

            return DigitalOceanService(self)
        elif self.provider == self.ProviderChoices.HETZNER:
            from proxies.proxies.services.hetzner import HetznerService

            return HetznerService(self)

    def create_server(self) -> bool:
        """Create proxy server."""
        return self.get_service().create_proxy()

    def delete_server(self) -> bool:
        """Delete proxy server."""
        result = self.get_service().delete_proxy()
        if result:
            self.delete()
            return True
        return False

    def check_status(self) -> bool:
        """Check proxy status."""
        return self.get_service().check_proxy()

    def check_proxy_works_correct(self) -> bool:
        """
        Check if proxy works correctly.

        Check if proxy is ready to use and works correctly by sending request to
        httpbin and check if ip match proxy's IP.
        """
        logger.info("Checking if proxy %s works correctly.", self.name)
        try:
            r = httpx.post("https://httpbin.org/post", proxies=self.get_config(), timeout=5)
            r.raise_for_status()
        except Exception:
            logger.exception("Can't get proxy status from httpbin.org.")
            return False

        if r.json()["origin"] == self.ipaddress:
            logger.info("Proxy %s works OK.", self.name)
            return True
        logger.warning("Proxy %s doesn't work correctly.", self.name)
        return False

    def get_config(self) -> dict:
        """Return proxy connection strings for `http` and `https`."""
        connection_string = (
            f"http://{settings.PROXY_LOGIN}:{settings.PROXY_PASSWORD}@{self.ipaddress}:{settings.PROXY_PORT}"
        )
        return {"http://": connection_string, "https://": connection_string}


class Client(UUIDModel):
    """Client."""

    name = models.CharField(max_length=64, unique=True)
    blacklisted_proxies = models.ManyToManyField(Proxy, related_name="blacklisted_clients", blank=True)
    default_proxy = models.ForeignKey(
        Proxy,
        related_name="default_clients",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "client"
        verbose_name_plural = "clients"

    def __str__(self) -> str:
        """Return client name."""
        return self.name
