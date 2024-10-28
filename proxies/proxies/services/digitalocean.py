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


DO_PROXY_DROPLET_USER_DATA = f"""
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


class DigitalOceanService(BaseService):
    """DigitalOcean service for proxies."""

    def create_proxy(self) -> bool:
        """Create new droplet."""
        logger.info("Creating droplet %s.", self.proxy.name)
        payload = {
            "name": self.proxy.name,
            "region": settings.DO_PROXY_DROPLET_REGION,
            "size": settings.DO_PROXY_DROPLET_SIZE,
            "image": settings.DO_PROXY_DROPLET_IMAGE,
            "ssh_keys": [],
            "backups": False,
            "ipv6": False,
            "monitoring": False,
            "tags": [settings.PROJECT_NAME, f"{settings.PROJECT_NAME}:proxy"],
            "user_data": DO_PROXY_DROPLET_USER_DATA,
        }

        self.proxy.create_request_at = timezone.now()
        try:
            r = httpx.post(
                "https://api.digitalocean.com/v2/droplets/",
                auth=TokenAuth(settings.DO_TOKEN),
                json=payload,
                timeout=10,
            )
            r.raise_for_status()
        except Exception:
            logger.exception("Request error on creating droplet %s", self.proxy.name)
            self.proxy.create_response = {"exception": traceback.format_exc()}
            self.proxy.save()
            return False

        data = r.json()
        self.proxy.create_response = data
        self.proxy.server_id = data["droplet"]["id"]
        self.proxy.save()
        logger.info("Droplet %s created.", self.proxy.name)

        # move to project
        payload = {
            "resources": [
                f"do:droplet:{self.proxy.server_id}",
            ]
        }
        try:
            r = httpx.post(
                f"https://api.digitalocean.com/v2/projects/{settings.DO_PROJECT_ID}/resources",
                auth=TokenAuth(settings.DO_TOKEN),
                json=payload,
                timeout=10,
            )
            r.raise_for_status()
        except Exception:
            logger.exception("Can't move droplet %s to selected project", self.proxy.name)

        return True

    def check_proxy(self) -> bool:
        """Check status of droplet."""
        logger.info("Checking droplet %s status.", self.proxy.name)
        self.proxy.last_check_at = timezone.now()

        try:
            r = httpx.get(
                f"https://api.digitalocean.com/v2/droplets/{self.proxy.server_id}",
                auth=TokenAuth(settings.DO_TOKEN),
                timeout=10,
            )
        except Exception:
            # request error... set proxy as inactive
            logger.exception("Can't get droplet %s status.", self.proxy.name)
            self.proxy.last_check_response = {"exception": traceback.format_exc()}
            self.proxy.active = False
            self.proxy.ipaddress = None
            self.proxy.save()
            return False

        data = r.json()
        self.proxy.last_check_response = data

        if r.status_code == 200:
            if data["droplet"]["status"] == "active":
                for ip in data["droplet"]["networks"]["v4"]:
                    if ip["type"] == "public" and "ip_address" in ip and ip["ip_address"]:
                        # proxy has ip address... set ip and check if is active
                        self.proxy.ipaddress = ip["ip_address"]
                        self.proxy.save()
                        logger.info("Droplet %s is ready.", self.proxy.name)
                        self.proxy.active = self.proxy.check_proxy_works_correct()
                        self.proxy.save()
                        return True

        # not valid...
        logger.warning("Droplet %s is not ready.", self.proxy.name)
        self.proxy.active = False
        self.proxy.ipaddress = None
        self.proxy.save()
        return False

    def delete_proxy(self) -> bool:
        """Delete existing droplet."""
        logger.info("Deleting droplet %s.", self.proxy.name)
        r = httpx.delete(
            f"https://api.digitalocean.com/v2/droplets/{self.proxy.server_id}",
            auth=TokenAuth(settings.DO_TOKEN),
            timeout=10,
        )
        if r.status_code == 204:
            logger.info("Droplet %s deleted.", self.proxy.name)
            return True
        else:
            logger.critical(
                "Can't delete droplet %s. Status Code: %s; Response: %s.",
                self.proxy.name,
                r.status_code,
                json.dumps(r.json()),
            )
            return False

    @classmethod
    def get_existing_proxies(cls) -> bool:
        """Get existing proxies from DO."""
        logger.info("Getting existing proxies.")
        params: dict[str, str] = {"tag_name": f"{settings.PROJECT_NAME}:proxy", "per_page": "50"}
        try:
            r = httpx.get(
                "https://api.digitalocean.com/v2/droplets",
                params=params,
                auth=TokenAuth(settings.DO_TOKEN),
                timeout=10,
            )
            r.raise_for_status()
        except Exception:
            logger.exception("Can't get existing proxies.")
            return False

        logger.info("Found %s existing proxies.", len(r.json()["droplets"]))

        Proxy.objects.filter(provider=Proxy.ProviderChoices.DIGITALOCEAN).update(is_removed=True)

        for droplet in r.json()["droplets"]:
            # get ip address
            ipaddress = None
            for ip in droplet["networks"]["v4"]:
                if ip["type"] == "public" and "ip_address" in ip and ip["ip_address"]:
                    ipaddress = ip["ip_address"]
                    break
            logger.info("Found proxy %s", droplet["name"])
            proxy: Proxy
            proxy, created = Proxy.objects.update_or_create(
                name=droplet["name"],
                provider=Proxy.ProviderChoices.DIGITALOCEAN,
                defaults={
                    "server_id": droplet["id"],
                    "ipaddress": ipaddress,
                    "create_request_at": dateutil.parser.parse(droplet["created_at"]),
                    "is_removed": False,
                },
            )

            if created:
                logger.info("Proxy %s newly created.", droplet["name"])
                proxy.active = proxy.check_proxy_works_correct()
                proxy.last_check_at = timezone.now()
                proxy.save()

        Proxy.objects.filter(provider=Proxy.ProviderChoices.DIGITALOCEAN, is_removed=True).delete()
        return True
