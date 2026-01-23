from celery import shared_task
import random

from django.conf import settings
from apps.common.redis import redis_client  

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

    # For now just log (later SMS / WhatsApp / Email)
    print(f"[OTP] tenant={tenant_id} phone={phone_number} otp={otp}")

    return True


@shared_task
def otp_cleanup_task():
    keys = redis_client.keys("otp:*")
    for key in keys:
        ttl = redis_client.ttl(key)
        if ttl == -1:
            redis_client.delete(key)