import os
import tempfile

import boto3
from app.core.config import settings
from botocore.exceptions import ClientError


class S3Service:
    """Download files from AWS S3 to a local temp path."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.bucket = settings.aws_storage_bucket_name

    def download_file(self, s3_key: str) -> str:
        """
        Download a file from S3 and return the local temp file path.
        Caller is responsible for deleting the temp file after use.
        """
        suffix = os.path.splitext(s3_key)[1] or ".pdf"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp.name
        tmp.close()

        try:
            self.client.download_file(self.bucket, s3_key, tmp_path)
        except ClientError as e:
            os.unlink(tmp_path)
            raise RuntimeError(f"Failed to download '{s3_key}' from S3: {e}") from e

        return tmp_path
