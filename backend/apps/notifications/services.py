from apps.notifications.models import Notification


def create_notification(*, tenant, user, type, message):
    Notification.objects.create(tenant=tenant, user=user, type=type, message=message)
