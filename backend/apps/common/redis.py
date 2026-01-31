# apps/common/redis.py
import os

try:
    import redis
except ImportError:
    redis = None

REDIS_URL = os.environ.get("REDIS_URL")

redis_client = None

if REDIS_URL and redis:
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        ssl_cert_reqs=None,
    )
