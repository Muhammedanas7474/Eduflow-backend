from rest_framework import serializers

from .models import Course, Lesson, LessonResource


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_active",
            "is_approved",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_active",
            "is_approved",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

        read_only_fields = ["id", "created_at", "updated_at", "created_by"]


class LessonResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonResource
        fields = ["id", "lesson", "title", "file_url", "file_type", "created_at"]
        read_only_fields = ["id", "created_at"]


class LessonSerializer(serializers.ModelSerializer):
    resources = LessonResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "video_url",
            "order",
            "is_active",
            "created_at",
            "resources",
        ]
        read_only_fields = ["id", "created_at"]
