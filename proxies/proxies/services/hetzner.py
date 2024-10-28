from __future__ import annotations

import json
import logging
import traceback

from django.conf import settings
from django.utils import timezone

import dateutil.parser
import httpx

from proxies.proxies.models import Proxy
from proxies.proxies.services.auth import TokenAuth
from proxies.proxies.services.base import BaseService

logger = logging.getLogger(__name__)


HETZNER_PROXY_SERVER_USER_DATA = f"""
#cloud-config
packages:
  - squid
  - httpd-tools

write_files:
  - path: /etc/squid/squid.conf
    content: |
      auth_param basic program /usr/lib64/squid/basic_ncsa_auth  /etc/squid/passwords
      auth_param basic realm proxy
      acl authenticated proxy_auth REQUIRED
      http_access allow authenticated
      http_port {settings.PROXY_PORT}
      forwarded_for delete
      via off
      follow_x_forwarded_for deny all
      request_header_access X-Forwarded-For deny all
      header_access X_Forwarded_For deny all
  - path: /etc/cron.daily/update.sh
    content: |
      #!/bin/bash
      /usr/bin/yum -y update
      systemctl restart squid

runcmd:
  - htpasswd -nb {settings.PROXY_LOGIN} {settings.PROXY_PASSWORD} >> /etc/squid/passwords
  - chmod a+x /etc/cron.daily/update.sh
  - systemctl start squid
  - systemctl enable squid
"""


class HetznerService(BaseService):
    """Hetzner service for creating, checking and deleting proxies."""

    def create_proxy(self) -> bool:
        """Create server on Hetzner."""
        logger.info("Creating Hetzner server %s.", self.proxy.name)
        payload = {
            "image": settings.HETZNER_PROXY_SERVER_IMAGE,
            "name": self.proxy.name,
            "server_type": settings.HETZNER_PROXY_SERVER_TYPE,
            "location": settings.HETZNER_PROXY_SERVER_LOCATION,
            "user_data": HETZNER_PROXY_SERVER_USER_DATA,
            "labels": {
                settings.PROJECT_NAME: "",
                f"{settings.PROJECT_NAME}/proxy": "",
            },
            "public_net": {
                "enable_ipv6": False,
            },
        }

        self.proxy.create_request_at = timezone.now()
        try:
            r = httpx.post(
                "https://api.hetzner.cloud/v1/servers",
                auth=TokenAuth(settings.HETZNER_TOKEN),
                json=payload,
                timeout=10,
            )
            r.raise_for_status()
        except Exception:
            logger.exception("Request error on creating Hetzner server %s", self.proxy.name)
            self.proxy.create_response = {"exception": traceback.format_exc()}
            self.proxy.save()
            return False

        data = r.json()
        self.proxy.create_response = data
        self.proxy.server_id = data["server"]["id"]
        self.proxy.save()
        logger.info("Server %s created.", self.proxy.name)
        return True

    def check_proxy(self) -> bool:
        """Check if server is ready."""
        logger.info("Checking Server %s status.", self.proxy.name)
        self.proxy.last_check_at = timezone.now()

        try:
            r = httpx.get(
                f"https://api.hetzner.cloud/v1/servers/{self.proxy.server_id}",
                auth=TokenAuth(settings.HETZNER_TOKEN),
                timeout=10,
            )
        except Exception:
            # request error... set proxy as inactive
            logger.exception("Can't get server %s status.", self.proxy.name)
            self.proxy.last_check_response = {"exception": traceback.format_exc()}
            self.proxy.active = False
            self.proxy.ipaddress = None
            self.proxy.save()
            return False

        data = r.json()
        self.proxy.last_check_response = data

        if r.status_code == 200:
            if data["server"]["status"] == "running":
                if data["server"]["public_net"]["ipv4"]["ip"]:
                    # proxy has ip address... set ip and check if is active
                    self.proxy.ipaddress = data["server"]["public_net"]["ipv4"]["ip"]
                    self.proxy.save()
                    logger.info("Server %s is ready.", self.proxy.name)
                    self.proxy.active = self.proxy.check_proxy_works_correct()
                    self.proxy.save()
                    return True

        # not valid...
        logger.warning("Server %s is not ready.", self.proxy.name)
        self.proxy.active = False
        self.proxy.ipaddress = None
        self.proxy.save()
        return False

    def delete_proxy(self) -> bool:
        """Delete server from Hetzner."""
        logger.info("Deleting server %s.", self.proxy.name)
        r = httpx.delete(
            f"https://api.hetzner.cloud/v1/servers/{self.proxy.server_id}",
            auth=TokenAuth(settings.HETZNER_TOKEN),
            timeout=10,
        )
        data = r.json()

        if "action" in data and "status" in data["action"] and data["action"]["status"] == "success":
            logger.info("Server %s is deleted.", self.proxy.name)
            return True
        else:
            logger.critical(
                "Can't delete server %s. Status Code: %s; Response: %s.",
                self.proxy.name,
                r.status_code,
                json.dumps(r.json()),
            )
            return False

    @classmethod
    def get_existing_proxies(cls) -> bool:
        """Get existing proxies from Hetzner."""
        logger.info("Getting existing Hetzner proxies.")

        params: dict[str, str] = {"label_selector": f"{settings.PROJECT_NAME}/proxy", "per_page": "50"}
        try:
            r = httpx.get(
                "https://api.hetzner.cloud/v1/servers",
                params=params,
                auth=TokenAuth(settings.HETZNER_TOKEN),
                timeout=10,
            )
            r.raise_for_status()
        except Exception:
            logger.exception("Can't get existing Hetzner proxies.")
            return False

        logger.info("Found %s existing Hetzner proxies.", len(r.json()["servers"]))

        Proxy.objects.filter(provider=Proxy.ProviderChoices.HETZNER).update(is_removed=True)

        for server in r.json()["servers"]:
            server_id = server["id"]
            create_request_at = dateutil.parser.parse(server["created"])
            name = server["name"]
            ipaddress = server["public_net"]["ipv4"]["ip"]

            logger.info("Found proxy %s", name)
            proxy: Proxy
            proxy, created = Proxy.objects.update_or_create(
                server_id=server_id,
                provider=Proxy.ProviderChoices.HETZNER,
                defaults={
                    "name": name,
                    "ipaddress": ipaddress,
                    "create_request_at": create_request_at,
                    "is_removed": False,
                },
            )

            if created:
                logger.info("Proxy %s newly created.", name)
                proxy.active = proxy.check_proxy_works_correct()
                proxy.last_check_at = timezone.now()
                proxy.save()

        Proxy.objects.filter(provider=Proxy.ProviderChoices.HETZNER, is_removed=True).delete()
        return True
