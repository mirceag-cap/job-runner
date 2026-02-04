import redis
from worker.core.config import settings
from worker.core.redis import QUEUE_NAME

client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

def pop_job_id(timeout_seconds: int) -> str | None:
    """
     BRPOP returns (key, value) or None on timeout.
    """
    item = client.brpop(QUEUE_NAME, timeout=timeout_seconds)
    if item is None:
        return None
    _key, value = item
    return value