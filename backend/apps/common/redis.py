# apps/common/redis.py
import os

import redis

REDIS_URL = os.environ.get("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

redis_client = redis.Redis.from_url(
    REDIS_URL, decode_responses=True, ssl_cert_reqs=None  # REQUIRED for Upstash
)
