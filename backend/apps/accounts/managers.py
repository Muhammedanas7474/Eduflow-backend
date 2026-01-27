from apps.tenants.models import Tenant
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone_number, tenant, password=None):
        if not phone_number:
            raise ValueError("Phone number is required")

        if isinstance(tenant, int):
            tenant = Tenant.objects.get(id=tenant)

        user = self.model(
            phone_number=phone_number,
            tenant=tenant,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, tenant, password):
        user = self.create_user(phone_number, tenant, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
