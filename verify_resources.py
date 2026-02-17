import requests

# Configuration
BASE_URL = "http://localhost/api"
PHONE = "9999999999"
PASSWORD = "password123"
TENANT_ID = 1  # Update to 1 as per existing user


def login(phone, password, tenant_id):
    response = requests.post(
        f"{BASE_URL}/accounts/login/",
        json={"phone_number": phone, "password": password, "tenant_id": tenant_id},
    )
    if response.status_code == 200:
        return response.json()
    print(f"Login failed: {response.text}")
    return None


TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwODk1NDMyLCJpYXQiOjE3NzA4OTI3MzIsImp0aSI6ImRmZmNmYWEyMTc3YTQ4Y2Y5ZThkZTQ5MDMwNjMyYWUzIiwidXNlcl9pZCI6MiwidGVuYW50X2lkIjoxLCJyb2xlIjoiQURNSU4ifQ.HlRs1M5c2jgkKr8432JimteSvAppFMW9B1QmmHVeFco"


def verify_resources():
    # 1. Login (Skipped, using token)
    # auth = login(PHONE, PASSWORD, TENANT_ID)

    token = TOKEN
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get a course and lesson
    print("Fetching courses...")
    courses_res = requests.get(f"{BASE_URL}/courses/", headers=headers)
    if courses_res.status_code != 200:
        print(f"Failed to fetch courses: {courses_res.text}")
        return

    courses_data = courses_res.json()
    if isinstance(courses_data, dict) and "results" in courses_data:
        courses = courses_data["results"]
    else:
        courses = courses_data

    if not courses:
        print("No courses found. Create a course first.")
        print(courses_data)
        return

    course_id = None
    lesson_id = None

    for course in courses:
        c_id = course["id"]
        print(f"Checking course {c_id} for lessons...")

        l_res = requests.get(f"{BASE_URL}/lessons/?course={c_id}", headers=headers)
        if l_res.status_code != 200:
            continue

        l_data = l_res.json()
        if isinstance(l_data, dict) and "results" in l_data:
            l_list = l_data["results"]
        else:
            l_list = l_data

        if l_list:
            course_id = c_id
            lesson_id = l_list[0]["id"]
            print(f"Found lesson {lesson_id} in course {course_id}")
            break

    if not course_id or not lesson_id:
        print("No lessons found in any course.")
        return

    print(f"Using Course ID: {course_id}")
    print(f"Using Lesson ID: {lesson_id}")

    # 3. Create Resource
    print("Creating resource...")
    resource_data = {
        "lesson": lesson_id,
        "title": "Test Resource",
        "file_url": "https://example.com/test.pdf",
        "file_type": "pdf",
    }
    create_res = requests.post(
        f"{BASE_URL}/lesson-resources/", json=resource_data, headers=headers
    )
    if create_res.status_code == 201:
        print("Resource created successfully.")
        resource_id = create_res.json()["id"]
    else:
        print(f"Failed to create resource: {create_res.text}")
        return

    # 4. Verify Lesson contains resource
    # 4. Verify Lesson contains resource
    print("Verifying resource in lesson...")
    lesson_res = requests.get(
        f"{BASE_URL}/lessons/?course={course_id}", headers=headers
    )

    if lesson_res.status_code != 200:
        print(f"Failed to fetch lessons: {lesson_res.status_code}")
        print(lesson_res.text)
        return

    l_data = lesson_res.json()
    if isinstance(l_data, dict) and "results" in l_data:
        lessons = l_data["results"]
    else:
        lessons = l_data

    target_lesson = next(
        (lesson for lesson in lessons if lesson["id"] == lesson_id), None
    )

    if not target_lesson:
        print(f"Lesson {lesson_id} not found in course lessons.")
        return

    if target_lesson.get("resources") and len(target_lesson["resources"]) > 0:
        print("SUCCESS: Resource found in lesson details.")
        print(target_lesson["resources"])
    else:
        print("FAILURE: Resource NOT found in lesson details.")
        print(target_lesson)

    # 5. Delete Resource
    print("Deleting resource...")
    del_res = requests.delete(
        f"{BASE_URL}/lesson-resources/{resource_id}/", headers=headers
    )
    if del_res.status_code == 204:
        print("Resource deleted successfully.")
    else:
        print(f"Failed to delete resource: {del_res.text}")


if __name__ == "__main__":
    verify_resources()
