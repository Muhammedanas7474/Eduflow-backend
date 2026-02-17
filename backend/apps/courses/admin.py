from django.contrib import admin

from .models import Course, Lesson, Option, Question, Quiz


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


class OptionInline(admin.TabularInline):
    model = Option
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "tenant", "created_by", "created_at")
    list_filter = ("tenant", "created_at")
    search_fields = ("title",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_text", "quiz", "correct_answer")
    search_fields = ("question_text",)
    inlines = [OptionInline]
