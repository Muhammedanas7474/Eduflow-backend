# ruff: noqa: E402
import sys

sys.path.append("/app")
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")
django.setup()

from apps.accounts.models import User
from apps.chat.models import ChatMessage, ChatRoom, ChatRoomMember
from apps.courses.models import Course
from apps.tenants.models import Tenant


def setup():
    # 1. Create Tenant
    tenant, created = Tenant.objects.get_or_create(name="EduFlow Default")
    if created:
        print(f"Created Tenant: {tenant.name} (ID: {tenant.id})")
    else:
        print(f"Tenant already exists: {tenant.name} (ID: {tenant.id})")

    # 2. Create Superuser (Admin/Instructor)
    admin_phone = "7777777777"
    if not User.objects.filter(phone_number=admin_phone).exists():
        admin = User.objects.create_superuser(
            phone_number=admin_phone, password="test@123", tenant=tenant
        )
        admin.role = "ADMIN"
        admin.save()
        print(f"Created Superuser: {admin.phone_number} / test@123")
    else:
        admin = User.objects.get(phone_number=admin_phone)
        admin.set_password("test@123")
        admin.save()
        print(f"Updated Superuser password: {admin_phone} / test@123")

    # 3. Create Student User
    student_phone = "9999999999"
    if not User.objects.filter(phone_number=student_phone).exists():
        student = User.objects.create_user(
            phone_number=student_phone, password="test@123", tenant=tenant
        )
        student.role = "STUDENT"
        student.save()
        print(f"Created Student: {student.phone_number} / test@123")
    else:
        student = User.objects.get(phone_number=student_phone)
        student.set_password("test@123")
        student.save()
        print(f"Updated Student password: {student_phone} / test@123")

    # 4. Create Sample Course
    course_title = "Introduction to AI"
    course, created = Course.objects.get_or_create(
        title=course_title,
        tenant=tenant,
        defaults={
            "description": "Learn the basics of Artificial Intelligence.",
            "created_by": admin,
            "is_approved": True,
            "is_active": True,
        },
    )
    if created:
        print(f"Created Course: {course.title}")
    else:
        print(f"Course already exists: {course.title}")

    # 5. Create Course Chat Room
    room, created = ChatRoom.get_or_create_course_room(
        tenant.id, course.id, course.title
    )
    if created:
        print(f"Created Course Chat Room: {room.name}")

    # Add Admin and Student to Course Room
    ChatRoomMember.objects.get_or_create(room=room, user_id=admin.id)
    ChatRoomMember.objects.get_or_create(room=room, user_id=student.id)
    print("Added Admin and Student to Course Chat")

    # Add welcome message
    if not ChatMessage.objects.filter(room=room).exists():
        ChatMessage.objects.create(
            room=room,
            sender_id=admin.id,
            content=f"Welcome to the {course.title} course chat! Feel free to ask questions here.",
        )
        print("Added welcome message to Course Chat")

    # 6. Create DM Room between Admin and Student
    dm_room, created = ChatRoom.get_or_create_dm(tenant.id, admin.id, student.id)
    if created:
        print("Created DM Room between Admin and Student")
    else:
        # For existing DM rooms, we need to ensure we have the object to add messages
        dm_room = (
            ChatRoom.objects.filter(type="DM", members__user_id=admin.id)
            .filter(members__user_id=student.id)
            .first()
        )
        print("DM Room already exists")

    # Add DM messages if none exist
    if dm_room and not ChatMessage.objects.filter(room=dm_room).exists():
        ChatMessage.objects.create(
            room=dm_room,
            sender_id=student.id,
            content="Hello Instructor! I have a question about the first lesson.",
        )
        ChatMessage.objects.create(
            room=dm_room,
            sender_id=admin.id,
            content="Hi! Sure, I'd be happy to help. What's on your mind?",
        )
        print("Added sample messages to DM Room")


if __name__ == "__main__":
    setup()
