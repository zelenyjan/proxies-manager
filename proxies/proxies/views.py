from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from proxies.proxies.models import Client, Proxy
from proxies.proxies.serializers import ProxySerializer
from proxies.proxies.tasks import create_server


class ProxyViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Proxy view set."""

    serializer_class = ProxySerializer

    def get_queryset(self) -> QuerySet[Proxy]:
        """Return the queryset."""
        return Proxy.objects.filter(active=True)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create proxy."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = request.data["provider"]

        if (
            provider == Proxy.ProviderChoices.DIGITALOCEAN
            and Proxy.objects.filter(provider=provider).count() >= settings.DO_LIMIT
        ):
            raise ValidationError(f"You can't create more then {settings.DO_LIMIT} proxies for Digitalocean provider.")

        if (
            provider == Proxy.ProviderChoices.HETZNER
            and Proxy.objects.filter(provider=provider).count() >= settings.HETZNER_LIMIT
        ):
            raise ValidationError(f"You can't create more then {settings.HETZNER_LIMIT} proxies for Hetzner provider.")

        instance = serializer.save()
        headers = self.get_success_headers(serializer.data)
        transaction.on_commit(lambda: create_server.delay(instance.pk))
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ClientAPIView(APIView):
    """Client API view."""

    def _get_proxies(self, client: Client) -> QuerySet[Proxy]:
        proxies = Proxy.objects.filter(active=True).exclude(
            pk__in=client.blacklisted_proxies.all().values_list("id", flat=True)
        )
        return proxies

    def get(self, request: Request, name: str) -> Response:
        """Get proxies for client."""
        client, _ = Client.objects.get_or_create(name=name)
        proxies = self._get_proxies(client)
        return Response(ProxySerializer(proxies, many=True, context={"client": client}).data)

    def put(self, request: Request, name: str) -> Response:
        """Add proxy to client blacklist."""
        client, _ = Client.objects.get_or_create(name=name)
        proxy = Proxy.objects.get(pk=request.data["proxy_id"])

        if client.default_proxy and client.default_proxy.id == proxy.id:
            return Response({"detail": "You can't blacklist default proxy."}, status=status.HTTP_400_BAD_REQUEST)

        client.blacklisted_proxies.add(proxy)
        proxies = self._get_proxies(client)
        return Response(ProxySerializer(proxies, many=True).data)
