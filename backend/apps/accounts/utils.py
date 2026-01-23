from apps.common.redis import redis_client
from apps.accounts.tasks import send_otp_task

OTP_TTL = 300


def send_otp(tenant_id, phone, purpose):
    send_otp_task.delay(
        tenant_id=tenant_id,
        phone_number=phone,
        purpose=purpose.upper(),
    )


def get_otp(tenant_id, phone, purpose):
    key = f"otp:{tenant_id}:{phone}:{purpose.upper()}"
    return redis_client.get(key)


def delete_otp(tenant_id, phone, purpose):
    key = f"otp:{tenant_id}:{phone}:{purpose.upper()}"
    redis_client.delete(key)
