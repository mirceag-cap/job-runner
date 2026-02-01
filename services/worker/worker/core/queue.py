import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "jobrunner:queue")

redis = Redis.from_url(REDIS_URL, decode_responses=True)

async def dequeue_job_id(timeout_seconds: int = 30) -> str | None:
    # wait up to timeout_seconds for an item
    # returns (queue_name, value) or None if timeout
    item = await redis.brpop(QUEUE_NAME, timeout=timeout_seconds)
    if item is None:
        return None
    _, job_id = item
    return job_id