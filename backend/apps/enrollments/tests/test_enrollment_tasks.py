import pytest
from apps.enrollments.tasks import enrollment_approved_task


@pytest.mark.django_db
def test_enrollment_approved_task_returns_not_found():
    result = enrollment_approved_task(tenant_id=999, enrollment_id=999)

    assert result == "Enrollment not found"
