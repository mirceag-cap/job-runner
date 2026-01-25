import asyncio
import logging

from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from worker.core.config import settings
from worker.db.session import AsyncSessionLocal
from worker.db.claim import claim_one_job
from worker.jobs.handlers import handle_csv_summary
from worker.models.job import JobStatus
from worker.core.logging import setup_logging

log = logging.getLogger('worker')

async def process_one(db: AsyncSession) -> bool:
    job = await claim_one_job(db)
    if job is None:
        return False

    log.info("job_claimed", extra={"job_id": str(job.id), "job_type": job.type})

    try:
        if job.type == 'csv_summary':
            result = await handle_csv_summary(job)
        else:
            raise ValueError(f"Unknown job type: {job.type}")

        job.result = result
        job.status = JobStatus.succeeded
        job.error = None
        log.info("job_succeeded", extra={"job_id": str(job.id), "job_type": job.type})

    except Exception as e:
        job.status = JobStatus.failed
        job.error = str(e)
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.failed
            job.run_after = None
            log.error("job_failed_permanent", extra={"job_id": str(job.id), "attempts": job.attempts, "error": str(e)})
        else:
            job.status = JobStatus.queued
            backoff_seconds = min(60, 2 ** job.attempts)
            job.run_after = func.now() + timedelta(seconds=backoff_seconds)
            log.error("job_failed_retrying", extra={"job_id": str(job.id), "attempts": job.attempts, "backoff_seconds": backoff_seconds, "error": str(e)})
        log.error("job_failed", extra={"job_id": str(job.id), "error": str(e)})

    return True

async def worker_loop() -> None:
    while True:
        async with AsyncSessionLocal() as db:
            async with db.begin():
                did_work = await process_one(db)

        if not did_work:
            await asyncio.sleep(settings.poll_interval_seconds)

def main() -> None:
    setup_logging()
    asyncio.run(worker_loop())

if __name__ == "__main__":
    main()