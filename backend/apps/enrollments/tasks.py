import requests
from celery import shared_task


@shared_task
def sync_enrollment_to_realtime(
    user_id, course_id, tenant_id, course_name, instructor_id=None
):
    """
    Call Realtime Service Webhook to add user to course chat room.
    Also adds the instructor if provided.
    """
    # Realtime Service internal URL (within Docker network)
    # Using 'realtime' service name from docker-compose
    url = "http://realtime:8001/api/chat/webhook/enrollment/"

    payload = {
        "user_id": user_id,
        "course_id": course_id,
        "tenant_id": tenant_id,
        "course_name": course_name,
        "instructor_id": instructor_id,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return f"Synced user {user_id} to course {course_id} chat."
    except requests.RequestException as e:
        return f"Failed to sync enrollment: {str(e)}"


@shared_task
def enrollment_approved_task(tenant_id, enrollment_id):
    """
    Handle post-enrollment actions like sending confirmation emails.
    """
    from apps.enrollments.models import Enrollment
    from apps.notifications.sqs_publisher import publish_event

    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)

        # Prepare event data
        event_data = {
            "event_type": "enrollment_approved",
            "tenant_id": str(tenant_id),
            "email": enrollment.student.email,
            "payload": {
                "course_name": enrollment.course.title,
                "student_name": enrollment.student.full_name or "Student",
                "enrollment_id": str(enrollment.id),
            },
        }

        # Publish to SQS
        response = publish_event(event_data)

        msg = f"Enrollment {enrollment.id} approved for {enrollment.student.email}."
        if response and "MessageId" in response:
            msg += f" Email event published (MsgId: {response['MessageId']})"
        else:
            msg += " Failed to publish email event."

        return msg
    except Enrollment.DoesNotExist:
        return "Enrollment not found"


@shared_task
def pending_enrollment_reminder_task():
    """
    Find pending enrollment requests older than 24 hours
    and send a reminder to instructors/admins.
    """
    from datetime import timedelta

    from apps.enrollments.models import EnrollmentRequest
    from django.utils import timezone

    # Calculate threshold (24 hours ago)
    threshold = timezone.now() - timedelta(hours=24)

    # Find pending requests older than threshold
    pending_requests = EnrollmentRequest.objects.filter(
        status="PENDING", created_at__lte=threshold
    )

    count = pending_requests.count()
    if count == 0:
        return "No pending enrollments older than 24h."

    # In a real app, we would group by instructor and send emails.
    # For now, just log it.
    return f"Found {count} pending enrollment requests older than 24h."
