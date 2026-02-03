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

    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        # TODO: Send email
        return f"Enrollment {enrollment.id} approved for {enrollment.student.email}"
    except Enrollment.DoesNotExist:
        return "Enrollment not found"
