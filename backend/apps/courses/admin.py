from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Course, Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_active")
    list_filter = ("course", "is_active")
    ordering = ("course", "order")
