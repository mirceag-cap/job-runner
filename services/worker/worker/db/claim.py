import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models.job import Job, JobStatus


async def claim_job_by_id(db: AsyncSession, job_id: str) -> Job | None:
    now = datetime.now(timezone.utc)

    job_uuid = uuid.UUID(job_id)

    stmt = (
        select(Job)
        .where(Job.id == job_uuid)
        .where(Job.status == JobStatus.queued)
        .where((Job.run_after.is_(None)) | (Job.run_after <= now))
        .with_for_update(skip_locked=True)
    )

    res = await db.execute(stmt)
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