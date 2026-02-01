from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from worker.models.job import Job, JobStatus

async def claim_one_job(db: AsyncSession) -> Job | None:
    now = datetime.now(timezone.utc)

    statement = (
        select(Job)
        .where(Job.status == JobStatus.queued)
        .where((Job.run_after.is_(None)) | (Job.run_after <= datetime.now(timezone.utc)))
        .order_by(Job.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    res = await db.execute(statement)
    job = res.scalar_one_or_none()

    if job is None:
        return None

    job.status = JobStatus.running
    job.attempts += 1

    if job.started_at is None:
        job.started_at = now

    job.updated_at = now

    await db.flush()

    return job