from __future__ import annotations

from typing import Any

from django.db.models.signals import post_delete
from django.dispatch import receiver

from proxies.proxies.models import Proxy
from proxies.proxies.tasks import delete_server


@receiver(post_delete, sender=Proxy)
def proxy_post_delete(sender: type[Proxy], instance: Proxy, **kwargs: Any) -> None:
    """Delete server on post delete."""
    if instance.server_id and not instance.is_removed:
        delete_server.delay(instance.id)
