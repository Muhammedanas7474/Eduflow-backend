from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "tenant", "is_phone_verified", "is_active")
    search_fields = ("phone_number",)
    
