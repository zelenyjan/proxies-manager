from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


def trigger_error(request):
    """For testing Sentry."""
    return 1 / 0


urlpatterns = [
    path("sentry-debug/", trigger_error),
    path("api/proxies/", include("proxies.proxies.urls")),
    path(settings.DJANGO_ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT, show_indexes=False)
