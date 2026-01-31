import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import  Response

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobOut
from app.core.metrics import JOB_CREATED_TOTAL, JOB_GET_TOTAL, API_REQUEST_DURATION_SECONDS

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
    start = time.perf_counter()
    job = Job(
        type=job_in.type,
        payload=job_in.payload,
        status=JobStatus.queued,
    )
    JOB_CREATED_TOTAL.labels(job_type=job_in.type).inc()
    db.add(job)
    await db.commit()
    await db.refresh(job)
    API_REQUEST_DURATION_SECONDS.labels(method="POST", path="/jobs").observe(
        time.perf_counter() - start
    )

    return job

@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    start = time.perf_counter()
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    JOB_GET_TOTAL.inc()
    API_REQUEST_DURATION_SECONDS.labels(method="GET", path="/jobs/{id}").observe(
        time.perf_counter() - start
    )
    return job

@router.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(
        content=data,
        media_type=CONTENT_TYPE_LATEST
    )