from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.enrollments.models import EnrollmentRequest
from apps.accounts.models import User
from apps.courses.models import Course
from apps.enrollments.models import Enrollment


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10},
)
def enrollment_approved_task(self, tenant_id, enrollment_id):
    """
    Runs AFTER admin approves enrollment
    """

    enrollment = Enrollment.objects.select_related(
        "student", "course"
    ).filter(
        id=enrollment_id,
        tenant_id=tenant_id,
    ).first()

    if not enrollment:
        return "Enrollment not found"

    student = enrollment.student
    course = enrollment.course

    # 🔔 Student notification (placeholder)
    print(
        f"[ENROLLMENT APPROVED] "
        f"Student={student.phone_number} "
        f"Course={course.title}"
    )

    # 🔔 Instructor notification (placeholder)
    if course.created_by:
        print(
            f"[INSTRUCTOR NOTIFY] "
            f"Instructor={course.created_by.phone_number} "
            f"Student={student.phone_number}"
        )

    # 📊 Analytics / audit hook
    print(
        f"[ANALYTICS] "
        f"tenant={tenant_id} "
        f"enrollment_id={enrollment_id} "
        f"time={timezone.now()}"
    )

    return "Enrollment approval notifications sent"


@shared_task
def pending_enrollment_reminder_task():
    cutoff_time = timezone.now() - timedelta(hours=24)

    pending_requests = EnrollmentRequest.objects.filter(
        status="PENDING",
        requested_at__lte=cutoff_time
    ).select_related("student", "course")

    for req in pending_requests:
        print(
            f"[REMINDER] Pending enrollment | "
            f"Student={req.student.phone_number} | "
            f"Course={req.course.title}"
        )