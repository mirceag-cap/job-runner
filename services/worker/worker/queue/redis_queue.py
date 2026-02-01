import json
import redis

from worker.core.config import settings

client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

QUEUE_KEY = "jobrunner:queue"

def pop_job_id(timeout_seconds: int) -> str | None:
    """
     BRPOP returns (key, value) or None on timeout.
    """
    item = client.brpop(QUEUE_KEY, timeout=timeout_seconds)
    if item is None:
        return None
    _key, value = item
    return value