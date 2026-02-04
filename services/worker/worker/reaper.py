import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from worker.db.session import AsyncSessionLocal
from worker.models.job import Job, JobStatus
from worker.core.redis import redis_client, QUEUE_NAME, PROCESSING_NAME


async def requeue_stuck_jobs() -> None:
    """
    Watchdog.
    Requeues jobs that are stuck in processing but are still queued in DB
    and ready to run.
    """
    while True:
        items = await redis_client.lrange(PROCESSING_NAME, 0, -1)
        if items:
            now = datetime.now(timezone.utc)
            async with AsyncSessionLocal() as db:
                for job_id_str in items:
                    try:
                        job_uuid = uuid.UUID(job_id_str)
                    except ValueError:
                        # garbage in redis -> drop it
                        await redis_client.lrem(PROCESSING_NAME, 1, job_id_str)
                        continue

                    res = await db.execute(select(Job).where(Job.id == job_uuid))
                    job = res.scalar_one_or_none()
                    if job is None:
                        # job deleted? drop it from processing
                        await redis_client.lrem(PROCESSING_NAME, 1, job_id_str)
                        continue

                    # Only requeue if DB says it's queued and it's eligible to run now
                    if job.status == JobStatus.queued and (job.run_after is None or job.run_after <= now):
                        # push back to queue and remove from processing
                        await redis_client.rpush(QUEUE_NAME, job_id_str)
                        await redis_client.lrem(PROCESSING_NAME, 1, job_id_str)

        await asyncio.sleep(5)