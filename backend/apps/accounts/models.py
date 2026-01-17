from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.tenants.models import Tenant
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)


    ROLE_CHOICES = (
    ("ADMIN", "Admin"),
    ("INSTRUCTOR", "Instructor"),
    ("STUDENT", "Student"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="STUDENT"
    )


    phone_number = models.CharField(max_length=15, unique=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users"
    )

    is_phone_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["tenant"]

    def __str__(self):
        return self.phone_number
    

