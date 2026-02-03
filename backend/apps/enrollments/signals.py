from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Enrollment
from .tasks import sync_enrollment_to_realtime


@receiver(post_save, sender=Enrollment)
def sync_enrollment_to_chat(sender, instance, created, **kwargs):
    if created and instance.is_active:
        # Get instructor ID from the course creator
        instructor_id = None
        if instance.course.created_by:
            instructor_id = instance.course.created_by.id

        sync_enrollment_to_realtime.delay(
            user_id=instance.student.id,
            course_id=instance.course.id,
            tenant_id=instance.tenant.id,
            course_name=instance.course.title,
            instructor_id=instructor_id,
        )
