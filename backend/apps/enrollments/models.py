from django.db import models
from apps.tenants.models import Tenant
from apps.accounts.models import User
from apps.courses.models import Course
from apps.courses.models import Lesson
from django.utils import timezone

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



class LessonProgress(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress"
    )

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "student", "lesson")

    def mark_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.student.phone_number} - {self.lesson.title}"