# ruff: noqa: E402

import os
import sys

import django

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")
django.setup()

from apps.courses.models import Lesson


def check_resources():
    print("--- Checking Lesson Resources ---")
    lessons = Lesson.objects.all()
    for lesson in lessons:
        resources = lesson.resources.all()
        if resources.exists():
            print(f"Lesson: {lesson.title} (ID: {lesson.id})")
            for res in resources:
                print(
                    f"  - Resource: {res.title} (Type: {res.file_type}) URL: {res.file_url}"
                )
        else:
            # print(f"Lesson: {lesson.title} has no resources")
            pass


if __name__ == "__main__":
    check_resources()
