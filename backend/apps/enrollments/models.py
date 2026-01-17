from django.db import models
from apps.tenants.models import Tenant
from apps.accounts.models import User
from apps.courses.models import Course


class Enrollment(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant", "student", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.phone_number} → {self.course.title}"
