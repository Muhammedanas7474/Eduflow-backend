import logging
import random

from apps.common.redis import redis_client
from celery import shared_task

logger = logging.getLogger(__name__)

OTP_EXPIRY_SECONDS = 300


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def send_otp_task(self, tenant_id, phone_number, purpose):
    """
    purpose:
    - REGISTER
    - LOGIN
    - FORGOT_PASSWORD
    """

    otp = random.randint(100000, 999999)

    redis_key = f"otp:{tenant_id}:{phone_number}:{purpose}"

    redis_client.setex(
        redis_key,
        OTP_EXPIRY_SECONDS,
        otp,
    )

    # Log OTP prominently — visible via: docker compose logs -f celery_worker
    logger.info("=" * 50)
    logger.info(f"[OTP] tenant={tenant_id} phone={phone_number} otp={otp}")
    logger.info(f"[OTP] redis_key={redis_key}")
    logger.info("=" * 50)

    return True


@shared_task
def otp_cleanup_task():
    keys = redis_client.keys("otp:*")
    for key in keys:
        ttl = redis_client.ttl(key)
        if ttl == -1:
            redis_client.delete(key)
