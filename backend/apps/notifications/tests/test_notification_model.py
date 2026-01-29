import pytest
from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.tenants.models import Tenant


@pytest.mark.django_db
def test_notification_creation():
    tenant = Tenant.objects.create(name="Test Tenant")

    user = User.objects.create(tenant=tenant, phone_number="7777777777", role="STUDENT")

    notification = Notification.objects.create(
        tenant=tenant,
        user=user,
        type="ENROLLMENT_APPROVED",
        message="You are enrolled successfully",
    )

    assert notification.id is not None
    assert notification.user == user
    assert notification.tenant == tenant
    assert notification.type == "ENROLLMENT_APPROVED"
    assert notification.is_read is False
