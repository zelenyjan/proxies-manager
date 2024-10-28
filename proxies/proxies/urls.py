from __future__ import annotations

from django.urls import path

from rest_framework.routers import SimpleRouter

from proxies.proxies.views import ClientAPIView, ProxyViewSet

app_name = "proxies"

router = SimpleRouter()
router.register("proxies", ProxyViewSet, basename="proxy")
urlpatterns = router.urls

urlpatterns += [
    path("client/<str:name>/", ClientAPIView.as_view(), name="client"),
]
