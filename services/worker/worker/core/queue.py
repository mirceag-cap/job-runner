import os
from redis.asyncio import Redis
from worker.core.redis import REDIS_URL, QUEUE_NAME
redis = Redis.from_url(REDIS_URL, decode_responses=True)

async def dequeue_job_id(timeout_seconds: int = 30) -> str | None:
    # wait up to timeout_seconds for an item
    # returns (queue_name, value) or None if timeout
    item = await redis.brpop(QUEUE_NAME, timeout=timeout_seconds)
    if item is None:
        return None
    _, job_id = item
    return job_id