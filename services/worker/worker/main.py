import asyncio
import logging

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

        job.error = str(e)  # Save error message so API can show why it failed

        # If we still have retries left, re-queue the job with a delay

        if job.attempts < job.max_attempts:

            from datetime import datetime, timezone, timedelta  # Time utilities

            from worker.core.retry import compute_backoff_seconds  # Backoff helper

            delay = compute_backoff_seconds(  # Compute how long to wait before retrying

                attempts=job.attempts,  # attempts is already incremented when claiming

                base=settings.retry_base_delay_seconds,  # e.g. 2 seconds

                cap=settings.retry_max_delay_seconds,  # e.g. 60 seconds

            )

            job.status = JobStatus.queued  # Put it back so it can be claimed later

            job.run_after = datetime.now(timezone.utc) + timedelta(seconds=delay)  # Schedule the retry time

            log.warning(
                "job_retry_scheduled",
                extra={
                    "job_id": str(job.id),
                    "attempts": job.attempts,

                    "max_attempts": job.max_attempts,

                    "delay_seconds": delay,

                    "error": str(e),

                },

            )

        else:

            job.status = JobStatus.failed

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