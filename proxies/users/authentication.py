from __future__ import annotations

from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """Bearer token authentication."""

    keyword = "Bearer"
