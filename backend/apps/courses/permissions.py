from rest_framework.permissions import BasePermission


class IsAdminOrInstructor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "ADMIN",
            "INSTRUCTOR",
        ]
