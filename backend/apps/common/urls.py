from django.urls import path
from apps.common.views import S3PresignUploadAPIView

urlpatterns = [
    path("uploads/presign/", S3PresignUploadAPIView.as_view()),
]
