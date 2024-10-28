from __future__ import annotations

from abc import ABC, abstractmethod

from proxies.proxies.models import Proxy


class BaseService(ABC):
    """Base service."""

    def __init__(self, proxy: Proxy):
        """Initialize."""
        self.proxy = proxy

    @abstractmethod
    def create_proxy(self) -> bool:
        """Create proxy."""
        ...

    @abstractmethod
    def check_proxy(self) -> bool:
        """Check proxy."""
        ...

    @abstractmethod
    def delete_proxy(self) -> bool:
        """Delete proxy from provider."""
        ...

    @classmethod
    @abstractmethod
    def get_existing_proxies(cls) -> bool:
        """Get existing proxies from provider."""
        ...
