import json
import logging
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import start_http_server

from worker.core.config import settings
from worker.core.redis import redis_client, QUEUE_KEY
from worker.db.session import AsyncSessionLocal
from worker.db.claim import claim_job_by_id
from worker.jobs.handlers import handle_csv_summary, handle_always_fail
from worker.models.job import JobStatus
from worker.core.logging import setup_logging
from worker.core.metrics import (
    WORKER_JOB_CLAIMED_TOTAL,
    WORKER_JOB_DURATION_SECONDS,
    WORKER_JOB_SUCCEEDED_TOTAL,
    WORKER_JOB_FAILED_TOTAL,
    WORKER_JOB_RETRY_SCHEDULED_TOTAL,
)
from worker.core.retry import compute_backoff_seconds
import time

log = logging.getLogger("worker")


async def process_job(db: AsyncSession, job_id: str) -> None:
    job = await claim_job_by_id(db, job_id)
    if job is None:
        # Concept: job can be missing/finished; queue is “at least once”
        log.info("job_not_claimed", extra={"job_id": job_id})
        return

    WORKER_JOB_CLAIMED_TOTAL.labels(job_type=job.type).inc()
    started = time.perf_counter()

    log.info("job_claimed", extra={"job_id": str(job.id), "job_type": job.type})

    now = datetime.now(timezone.utc)

    try:
        if job.type == "csv_summary":
            result = await handle_csv_summary(job)
        elif job.type == "always_fail":
            result = await handle_always_fail(job)
        else:
            raise ValueError(f"Unknown job type: {job.type}")

        job.result = result
        job.status = JobStatus.succeeded
        job.succeeded_at = now
        job.failed_at = None
        job.run_after = None
        job.error = None
        job.last_error = None
        job.last_error_at = None

        WORKER_JOB_SUCCEEDED_TOTAL.labels(job_type=job.type).inc()
        WORKER_JOB_DURATION_SECONDS.labels(job_type=job.type).observe(time.perf_counter() - started)
        log.info("job_succeeded", extra={"job_id": str(job.id), "job_type": job.type})

    except Exception as e:
        job.error = str(e)
        job.last_error = str(e)
        job.last_error_at = now

        if job.attempts < job.max_attempts:
            delay = compute_backoff_seconds(
                attempts=job.attempts,
                base=settings.retry_base_delay_seconds,
                cap=settings.retry_max_delay_seconds,
                jitter_ratio=settings.retry_jitter_ratio,
            )

            job.status = JobStatus.queued
            job.run_after = now + timedelta(seconds=delay)

            WORKER_JOB_RETRY_SCHEDULED_TOTAL.labels(job_type=job.type).inc()
            log.warning(
                "job_retry_scheduled",
                extra={
                    "job_id": str(job.id),
                    "attempts": job.attempts,
                    "max_attempts": job.max_attempts,
                    "delay_seconds": delay,
                    "run_after": job.run_after.isoformat(),
                    "error": str(e),
                },
            )

            # re-enqueue after delay.
            # sleep in a background task and push back.
            async def requeue_later():
                await asyncio.sleep(delay)
                await redis_client.rpush(QUEUE_KEY, str(job.id))

            asyncio.create_task(requeue_later())

        else:
            job.status = JobStatus.failed
            job.failed_at = now
            job.run_after = None

            WORKER_JOB_FAILED_TOTAL.labels(job_type=job.type).inc()
            log.error(
                "job_failed",
                extra={"job_id": str(job.id), "attempts": job.attempts, "max_attempts": job.max_attempts},
            )


async def worker_loop() -> None:
    while True:
        item = await redis_client.blpop(QUEUE_KEY, timeout=5)
        if item is None:
            continue

        _, raw = item
        try:
            job_id = parse_queue_item(raw)
        except Exception:
            log.exception("bad_queue_message", extra={"raw": raw})
            continue

        async with AsyncSessionLocal() as db:
            async with db.begin():
                await process_job(db, job_id)

def parse_queue_item(raw: str) -> str:
    raw = raw.strip()

    if raw.startswith("{"):
        data = json.loads(raw)
        raw = data["job_id"]

    # validate UUID and normalize
    return str(uuid.UUID(raw))


def main() -> None:
    setup_logging()
    start_http_server(settings.metrics_port)
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()