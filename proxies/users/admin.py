from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from proxies.users.models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    """Admin for User."""

    ordering = ["email"]
