import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "jobrunner:queue")

redis = Redis.from_url(REDIS_URL, decode_responses=True)

async def enqueue_job(job_id: str) -> None:
    # add job id to the queue list
    await redis.lpush(QUEUE_NAME, job_id)