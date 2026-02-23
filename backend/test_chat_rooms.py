# ruff: noqa: E402
import os
import sys

import django

# Setup Django environment
sys.path.append("/Users/m1/Desktop/BackeUp/Eduflow-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")
django.setup()

from apps.accounts.models import User
from apps.chat.views import RoomListView
from django.test import RequestFactory
from rest_framework.test import force_authenticate


def test_room_list_view():
    factory = RequestFactory()
    request = factory.get("/api/chat/rooms/")

    # Get the test user
    try:
        user = User.objects.get(phone_number="1234567890")
        print(
            f"Testing with user: {user.phone_number}, ID: {user.id}, Tenant: {user.tenant_id}"
        )
    except User.DoesNotExist:
        print("Test user not found")
        return

    # Use APIView.as_view() or instantiate View directly?
    # Better to use the view instance to replicate DRF behavior
    view = RoomListView.as_view()

    # Force authentication
    force_authenticate(request, user=user)

    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_room_list_view()
