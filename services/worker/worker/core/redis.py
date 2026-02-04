import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "jobrunner:queue")
PROCESSING_NAME = os.getenv("PROCESSING_NAME", "jobrunner:processing")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

async def reserve_job_id(timeout_seconds: int = 30) -> str | None:
    """
        Reservation = reliably take work.
        brpoplpush atomically moves one item from QUEUE_NAME
        to PROCESSING_NAME, so the job is not lost if the worker crashes.
        """
    job_id = await redis_client.brpoplpush(QUEUE_NAME, PROCESSING_NAME, timeout=timeout_seconds)
    return job_id

async def ack_job_id(job_id: str) -> None:
    """
        Ack = confirm job is fully processed.
        lrem removes ONE matching entry from processing list.
        """
    await redis_client.lrem(PROCESSING_NAME, 1, job_id)