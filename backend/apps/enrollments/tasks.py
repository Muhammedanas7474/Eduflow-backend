from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.enrollments.models import EnrollmentRequest, Enrollment
from apps.notifications.models import Notification


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

    # ===============================
    # 🔔 STUDENT NOTIFICATION (DB)
    # ===============================
    notification = Notification.objects.create(
        tenant_id=tenant_id,
        user=student,
        type="ENROLLMENT_APPROVED",
        message=f"You are enrolled in {course.title}",
    )

    # ===============================
    # 🔴 REALTIME PUSH (WebSocket)
    # ===============================
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{student.id}",
        {
            "type": "notify",
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
        }
    )

    # ===============================
    # 🔔 EXISTING LOGS (UNCHANGED)
    # ===============================
    print(
        f"[ENROLLMENT APPROVED] "
        f"Student={student.phone_number} "
        f"Course={course.title}"
    )

    if course.created_by:
        print(
            f"[INSTRUCTOR NOTIFY] "
            f"Instructor={course.created_by.phone_number} "
            f"Student={student.phone_number}"
        )

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
