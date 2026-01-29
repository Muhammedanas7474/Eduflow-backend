import pytest
from apps.accounts.models import User
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from apps.enrollments.tasks import enrollment_approved_task
from apps.tenants.models import Tenant


@pytest.mark.django_db
def test_enrollment_approved_task_success():
    """
    Happy path:
    Enrollment exists → task runs successfully
    """

    # Arrange
    tenant = Tenant.objects.create(name="Test Tenant")

    instructor = User.objects.create(
        tenant=tenant, phone_number="9999999999", role="INSTRUCTOR"
    )

    student = User.objects.create(
        tenant=tenant, phone_number="8888888888", role="STUDENT"
    )

    course = Course.objects.create(
        tenant=tenant, title="Django Mastery", created_by=instructor
    )

    enrollment = Enrollment.objects.create(
        tenant=tenant, student=student, course=course
    )

    # Act
    result = enrollment_approved_task(tenant_id=tenant.id, enrollment_id=enrollment.id)

    # Assert
    assert result == "Enrollment approval notifications sent"
