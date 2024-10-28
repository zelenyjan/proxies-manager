from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from celery.utils.log import get_task_logger

from config import celery
from proxies.proxies.models import Proxy
from proxies.proxies.services.digitalocean import DigitalOceanService
from proxies.proxies.services.hetzner import HetznerService

logger = get_task_logger(__name__)


@celery.task
def check_all_proxies() -> None:
    """
    Check all created proxies(droplets) if there are active on DO and proxy actually works.

    :return: None
    """
    proxy: Proxy
    state = {}
    for proxy in Proxy.objects.filter(server_id__isnull=False):
        state[proxy.id] = proxy.active

        if not proxy.active or (proxy.last_check_at + timedelta(hours=1) < timezone.now()):
            # check every run if not active otherwise once per hour
            proxy.check_status()

        if proxy.active and proxy.reported:
            # was reported but now is active so clear reported flag
            proxy.reported = False
            proxy.save()

        if (
            not proxy.active
            and not proxy.reported
            and (proxy.create_request_at + timedelta(minutes=10) < timezone.now())
        ):
            # create 10 minutes ago but still not active... report it
            logger.warning("Proxy %s created more then 10 minutes ago but still not active.", proxy.name)
            proxy.reported = True
            proxy.save()


@celery.task
def update_proxies_from_services() -> None:
    """Update proxies from services."""
    try:
        HetznerService.get_existing_proxies()
    except Exception:
        logger.exception("Error on updating proxies from Hetzner.")

    try:
        DigitalOceanService.get_existing_proxies()
    except Exception:
        logger.exception("Error on updating proxies from DigitalOcean.")


@celery.task
def create_server(instance_id: int) -> None:
    """Create proxy server."""
    proxy = Proxy.objects.get(pk=instance_id)
    proxy.create_server()


@celery.task
def delete_server(instance_id: int) -> None:
    """Delete proxy server."""
    proxy = Proxy.objects.get(pk=instance_id)
    proxy.delete_server()
