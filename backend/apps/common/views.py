import uuid

import boto3
from apps.common.exceptions import AppException
from apps.common.responses import success_response
from botocore.config import Config
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class S3PresignUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_name = request.data.get("file_name")
        content_type = request.data.get("content_type")

        if not file_name or not content_type:
            raise AppException("file_name and content_type are required")

        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION,
                endpoint_url=f"https://s3.{settings.AWS_S3_REGION}.amazonaws.com",
                config=Config(signature_version="s3v4"),
            )

            key = f"lessons/{uuid.uuid4()}-{file_name}"

            upload_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.AWS_S3_BUCKET_NAME,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=300,
            )

            file_url = (
                f"https://{settings.AWS_S3_BUCKET_NAME}"
                f".s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"
            )

            return Response(
                success_response(
                    data={
                        "upload_url": upload_url,
                        "file_url": file_url,
                    },
                    message="Presigned upload URL generated",
                )
            )

        except Exception as e:
            raise AppException(str(e))
