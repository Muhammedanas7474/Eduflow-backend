from apps.accounts.models import User
from apps.courses.models import Course, Lesson
from apps.tenants.models import Tenant
from django.db import models
from django.utils import timezone


class Enrollment(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="enrollments"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant", "student", "course")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.phone_number} → {self.course.title}"


class LessonProgress(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="progress"
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


class EnrollmentRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollment_requests"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollment_requests"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    requested_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_enrollment_requests",
    )

    class Meta:
        unique_together = ("tenant", "student", "course")

    def __str__(self):
        return f"{self.student.phone_number} → {self.course.title}"
