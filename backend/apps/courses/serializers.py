from rest_framework import serializers

from .models import Course, Lesson, LessonResource, Option, Question, Quiz


class CourseSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_active",
            "is_approved",
            "cover_theme",
            "category",
            "created_at",
            "updated_at",
            "created_by",
            "student_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def get_student_count(self, obj):
        return obj.enrollments.count()


class CourseListSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_active",
            "is_approved",
            "cover_theme",
            "category",
            "created_at",
            "updated_at",
            "created_by",
            "student_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def get_student_count(self, obj):
        return obj.enrollments.count()


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


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "option_text"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "question_text", "correct_answer", "options"]
        read_only_fields = ["id"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "course",
            "lesson",
            "title",
            "status",
            "created_by",
            "created_at",
            "questions",
        ]
        read_only_fields = ["id", "created_at", "created_by"]
