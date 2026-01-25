import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from worker.core.config import settings
from worker.db.session import AsyncSessionLocal
from worker.db.claim import claim_one_job
from worker.jobs.handlers import handle_csv_summary, handle_always_fail
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
        elif job.type == 'always_fail':
            result = await handle_always_fail(job)
        else:
            raise ValueError(f"Unknown job type: {job.type}")

        job.result = result
        job.status = JobStatus.succeeded
        job.error = None
        log.info("job_succeeded", extra={"job_id": str(job.id), "job_type": job.type})


    except Exception as e:
        job.error = str(e)
        if job.attempts < job.max_attempts:

            from worker.core.retry import compute_backoff_seconds

            delay = compute_backoff_seconds(
                attempts=job.attempts,
                base=settings.retry_base_delay_seconds,
                cap=settings.retry_max_delay_seconds,
                jitter_ratio=settings.retry_jitter_ratio
            )

            job.status = JobStatus.queued
            job.run_after = datetime.now(timezone.utc) + timedelta(seconds=delay)
            job.error = str(e)
            job.last_error = str(e)
            job.last_error_at = datetime.now(timezone.utc)
            log.warning(
                "job_retry_scheduled",
                extra={
                    "job_id": str(job.id),
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                    "delay_seconds": delay,
                    "run_after": job.run_after.isoformat() if job.run_after else None,
                    "error": str(e),
                },
            )
        else:
            job.status = JobStatus.failed
            job.failed_at = datetime.now(timezone.utc)
            log.error(
                "job_failed",
                extra={
                    "job_id": str(job.id),
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                    "error": str(e),
                },
            )
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