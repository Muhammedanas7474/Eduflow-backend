from apps.enrollments.models import Enrollment
from apps.enrollments.tasks import sync_enrollment_to_realtime
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync all active enrollments to the Realtime Chat Service"

    def handle(self, *args, **options):
        enrollments = Enrollment.objects.filter(is_active=True).select_related(
            "student", "course", "course__created_by", "tenant"
        )

        total = enrollments.count()
        self.stdout.write(f"Syncing {total} active enrollments...")

        synced = 0
        for enrollment in enrollments:
            try:
                instructor_id = None
                if enrollment.course.created_by:
                    instructor_id = enrollment.course.created_by.id

                sync_enrollment_to_realtime.delay(
                    user_id=enrollment.student.id,
                    course_id=enrollment.course.id,
                    tenant_id=enrollment.tenant.id,
                    course_name=enrollment.course.title,
                    instructor_id=instructor_id,
                )
                synced += 1
            except Exception as e:
                self.stderr.write(f"Failed to sync enrollment {enrollment.id}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully queued {synced}/{total} enrollments for sync."
            )
        )
