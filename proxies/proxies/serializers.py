from __future__ import annotations

from rest_framework import serializers

from proxies.proxies.models import Client, Proxy


class ProxySerializer(serializers.ModelSerializer):
    """Proxy serializer."""

    class Meta:
        model = Proxy
        fields = [
            "id",
            "server_id",
            "name",
            "ipaddress",
            "provider",
        ]
        read_only_fields = [
            "id",
            "server_id",
            "name",
            "ipaddress",
        ]

    def get_client_default(self, instance: Proxy) -> bool:
        """Return client default."""
        client: Client | None = self.context.get("client", None)
        return client and client.default_proxy == instance

    def get_fields(self):
        """Return fields."""
        fields = super().get_fields()
        if self.context.get("client", None):
            fields["client_default"] = serializers.SerializerMethodField(read_only=True)
        return fields
