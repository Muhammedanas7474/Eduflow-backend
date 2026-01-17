from django.contrib import admin
from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "tenant",
        "created_by",
        "is_active",
        "created_at",
    )
    list_filter = ("tenant", "is_active", "created_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
        "tenant",
        "order",
        "is_active",
        "created_at",
    )
    list_filter = ("tenant", "course", "is_active")
    search_fields = ("title",)
    ordering = ("course", "order")
    readonly_fields = ("created_at",)
