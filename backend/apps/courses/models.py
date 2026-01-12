from django.db import models
from apps.tenants.models import Tenant
from apps.accounts.models import User

class Course(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_courses"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    




class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    video_url = models.URLField()
    order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

