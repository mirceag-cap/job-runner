from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from worker.models.job import Job, JobStatus

async def claim_one_job(db: AsyncSession) -> Job | None:
    statement = (
        select(Job)
        .where(Job.status == JobStatus.queued)
        .where(or_(Job.run_after.is_(None), Job.run_after <= func.now()))
        .order_by(Job.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    res = await db.execute(statement)
    job = res.scalar_one_or_none()

    if job is None:
        return None

    job.status = JobStatus.running
    job.attempts += 1
    await db.flush()

    return job