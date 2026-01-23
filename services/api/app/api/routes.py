from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobOut

router = APIRouter()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/")
async def root():
    return {"service": "jobrunner-api", "docs": "/docs"}

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(job_in: JobCreate, db: AsyncSession = Depends(get_db)):
    job = Job(
        type=job_in.type,
        payload=job_in.payload,     # <-- dict
        status=JobStatus.queued,    # <-- enum
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job