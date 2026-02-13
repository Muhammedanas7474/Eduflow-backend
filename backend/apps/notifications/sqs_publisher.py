import json
import logging
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


def get_queue_region():
    """
    Extracts the region from the SQS Queue URL.
    Example: https://sqs.ap-south-1.amazonaws.com/... -> ap-south-1
    Fallback to settings.AWS_REGION if parsing fails.
    """
    queue_url = getattr(settings, "AWS_SQS_QUEUE_URL", "")
    if not queue_url:
        return settings.AWS_REGION

    try:
        # urlparse("https://sqs.ap-south-1.amazonaws.com/...")
        # netloc = "sqs.ap-south-1.amazonaws.com"
        domain_parts = urlparse(queue_url).netloc.split(".")
        if len(domain_parts) >= 4 and domain_parts[0] == "sqs":
            return domain_parts[1]
    except Exception:
        pass

    return settings.AWS_REGION


def get_sqs_client():
    region = get_queue_region()
    return boto3.client(
        "sqs",
        region_name=region,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def publish_event(event_data: dict):
    """
    Publishes an event to SQS for async notification processing.
    """
    try:
        sqs = get_sqs_client()
        queue_url = settings.AWS_SQS_QUEUE_URL

        if not queue_url:
            logger.error("AWS_SQS_QUEUE_URL is not set.")
            return None

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event_data),
        )
        return response

    except ClientError as e:
        logger.error(f"Failed to publish event to SQS: {e}")
        # Re-raise or handle gracefully depending on requirements.
        # For now, let's print error to console for visibility during dev as well
        print(f"SQS Publish Error: {e}")
        raise e
    except Exception as e:
        logger.exception("Unexpected error in publish_event")
        raise e
