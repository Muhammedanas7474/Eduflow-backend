import os


def setup():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")

    import django  # noqa: E402

    django.setup()

    from apps.accounts.models import User  # noqa: E402
    from apps.courses.models import Course, Lesson  # noqa: E402
    from apps.tenants.models import Tenant  # noqa: E402
    from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

    # 1. Create Tenant
    tenant, created = Tenant.objects.get_or_create(name="Test Tenant")
    print(f"Tenant ID: {tenant.id}")

    # 2. Create Instructor
    phone = "9999999999"
    password = "password123"

    try:
        user = User.objects.get(phone_number=phone)
        print("User exists.")
        if not user.check_password(password):
            user.set_password(password)
            user.save()
            print("Password updated.")
    except User.DoesNotExist:
        user = User.objects.create_user(
            phone_number=phone, password=password, tenant=tenant
        )
        user.full_name = "Test Instructor"
        user.role = "INSTRUCTOR"
        user.save()
        print("User created.")

    print(f"Phone: {phone}")
    print(f"Password: {password}")

    print("--- Existing Users ---")
    for u in User.objects.all():
        print(
            f"ID: {u.id}, Phone: {u.phone_number}, Tenant: {u.tenant.id} ({u.tenant.name})"
        )

    # Generate Token for Test User
    user = User.objects.get(phone_number=phone)
    refresh = RefreshToken.for_user(user)
    refresh["tenant_id"] = user.tenant_id
    refresh["role"] = user.role
    refresh["user_id"] = user.id
    print(f"\nACCESS_TOKEN: {str(refresh.access_token)}")

    courses = Course.objects.filter(tenant_id=tenant.id)
    print(f"\nTotal Courses: {courses.count()}")

    if not courses.exists():
        course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            created_by=user,
            tenant=tenant,
            is_active=True,
            is_approved=True,
        )
        print("Created Test Course.")
    else:
        course = courses.first()

    print(f"Course ID: {course.id}")
    lessons = Lesson.objects.filter(course=course)
    print(f"Lessons in Course {course.id}: {lessons.count()}")

    if not lessons.exists():
        Lesson.objects.create(
            course=course,
            title="Test Lesson",
            tenant=tenant,
            created_by=user,
            order=1,
            is_active=True,
        )
        print("Created Test Lesson.")


if __name__ == "__main__":
    setup()
