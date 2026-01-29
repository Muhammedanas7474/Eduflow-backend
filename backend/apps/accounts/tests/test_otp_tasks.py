from unittest.mock import patch

import pytest
from apps.accounts.tasks import OTP_EXPIRY_SECONDS, send_otp_task


@pytest.mark.django_db
def test_send_otp_task_generates_valid_otp():
    tenant_id = 1
    phone_number = "9999999999"
    purpose = "LOGIN"

    # 🔹 Mock redis_client.setex
    with patch("apps.accounts.tasks.redis_client") as mock_redis:
        result = send_otp_task(
            tenant_id=tenant_id,
            phone_number=phone_number,
            purpose=purpose,
        )

        # ✅ Function should return True
        assert result is True

        # ✅ Redis setex must be called once
        mock_redis.setex.assert_called_once()

        # 🔍 Inspect arguments passed to Redis
        args, kwargs = mock_redis.setex.call_args

        redis_key = args[0]
        ttl = args[1]
        otp = args[2]

        # ✅ Key format
        assert redis_key == f"otp:{tenant_id}:{phone_number}:{purpose}"

        # ✅ TTL is correct
        assert ttl == OTP_EXPIRY_SECONDS

        # ✅ OTP format
        assert isinstance(otp, int)
        assert 100000 <= otp <= 999999
