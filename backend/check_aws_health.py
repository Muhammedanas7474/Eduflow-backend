# ruff: noqa: E402

import os
import sys

import boto3
from botocore.exceptions import ClientError

# Setup environment to access Django settings
# Get the directory containing this script (which is .../backend)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the directory containing 'eduflow' package (which is current_dir) to sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")
import django
from django.conf import settings

django.setup()


def check_aws_health():
    print("\n" + "=" * 50)
    print("       AWS SERVICES HEALTH CHECK")
    print("=" * 50 + "\n")

    print("🔧 CONFIGURATION:")
    print(f"   - AWS_REGION (App): {settings.AWS_REGION}")
    print(f"   - SQS Queue URL:    {settings.AWS_SQS_QUEUE_URL}")
    print(f"   - S3 Bucket Name:   {settings.AWS_S3_BUCKET_NAME}")
    print("-" * 50)

    # ---------------------------------------------------------
    # 1. SQS CHECK
    # ---------------------------------------------------------
    print("\n1️⃣  Checking SQS (Notification Service)...")
    try:
        from apps.notifications.sqs_publisher import publish_event

        test_event = {
            "event_type": "health_check",
            "message": "Testing SQS Configuration",
        }

        response = publish_event(test_event)

        if response and "MessageId" in response:
            print("   ✅ SUCCESS: Message published to SQS.")
            print(f"      Message ID: {response['MessageId']}")
        else:
            print("   ❌ FAILED: Message sent but no ID returned.")
            print(f"      Response: {response}")

    except Exception as e:
        print("   ❌ FAILED: Could not publish to SQS.")
        print(f"      Error: {e}")

    # ---------------------------------------------------------
    # 2. S3 CHECK
    # ---------------------------------------------------------
    print("\n2️⃣  Checking S3 (File Storage)...")
    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        bucket_name = settings.AWS_S3_BUCKET_NAME
        test_file_key = "health_check_test_file.txt"

        # Check Upload
        s3.put_object(
            Bucket=bucket_name, Key=test_file_key, Body=b"S3 Health Check Passed"
        )
        print("   ✅ SUCCESS: 'put_object' worked (Upload successful).")

        # Check Download (Get Object)
        get_resp = s3.get_object(Bucket=bucket_name, Key=test_file_key)
        content = get_resp["Body"].read().decode("utf-8")
        if content == "S3 Health Check Passed":
            print("   ✅ SUCCESS: 'get_object' worked (Read successful).")
        else:
            print("   ⚠️ WARNING: 'get_object' Content mismatch.")

        # Check Cleanup (Delete)
        s3.delete_object(Bucket=bucket_name, Key=test_file_key)
        print("   ✅ SUCCESS: 'delete_object' worked (Cleanup successful).")

    except ClientError as e:
        print("   ❌ FAILED: S3 Operation failed.")
        print(f"      Error: {e}")
    except Exception as e:
        print("   ❌ FAILED: Unexpected error.")
        print(f"      Error: {e}")

    print("\n" + "=" * 50)
    print("             CHECK COMPLETE")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    check_aws_health()
