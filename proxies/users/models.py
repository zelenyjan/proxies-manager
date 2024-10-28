from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from model_utils.models import UUIDModel

from proxies.users.manager import CustomUserManager


class User(UUIDModel, AbstractUser):
    """Custom user model."""

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        ordering = ["email"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        """Return email as string representation."""
        return self.email
