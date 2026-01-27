from apps.common.views import S3PresignUploadAPIView
from django.urls import path

urlpatterns = [
    path("uploads/presign/", S3PresignUploadAPIView.as_view()),
]
