from django.db import models
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("ENROLLMENT", "Enrollment"),
        ("SYSTEM", "System"),
        ("COURSE", "Course"),
    )

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} → {self.user.phone_number}"
