from __future__ import annotations

from typing import override

import httpx


class TokenAuth(httpx.Auth):
    """Attaches a token to the request as an `Authorization` header."""

    def __init__(self, token):
        """Initialize the auth object."""
        self.token = token

    @override
    def auth_flow(self, request):
        """Send the request, with a custom `Authentication` header."""
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request
