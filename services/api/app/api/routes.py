import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import  Response, JSONResponse

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobOut
from app.schemas.result import JobResultOut
from app.core.metrics import JOB_CREATED_TOTAL, JOB_GET_TOTAL, API_REQUEST_DURATION_SECONDS
from app.core.queue import enqueue_job

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
async def create_job(
        job_in: JobCreate,
        db: AsyncSession = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")
):
    start = time.perf_counter()

    job = Job(
        type=job_in.type,
        payload=job_in.payload,
        status=JobStatus.queued,
        idempotency_key=idempotency_key,
    )

    db.add(job)

    try:
        await db.commit()
        await db.refresh(job)
        await enqueue_job(str(job.id))
        JOB_CREATED_TOTAL.labels(job_type=job_in.type).inc()
        API_REQUEST_DURATION_SECONDS.labels(method="POST", path="/jobs").observe(
            time.perf_counter() - start
        )

        return JSONResponse(status_code=201, content=jsonable_encoder(job))

    except IntegrityError:
        await db.rollback()
        if not idempotency_key:
            raise

        res = await db.execute(select(Job).where(Job.idempotency_key == idempotency_key))
        existing = res.scalar_one_or_none()

        if existing is None:
            raise HTTPException(status_code=500, detail="Idempotency conflict but job not found")

        if existing.status in (JobStatus.queued, JobStatus.running):
            await enqueue_job(str(existing.id))

        API_REQUEST_DURATION_SECONDS.labels(method="POST", path="/jobs").observe(
            time.perf_counter() - start
        )

        return JSONResponse(status_code=200, content=jsonable_encoder(existing))

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

@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str, db: AsyncSession = Depends(get_db)):
    start = time.perf_counter()

    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    API_REQUEST_DURATION_SECONDS.labels(method="GET", path="/jobs/{id}/result").observe(
        time.perf_counter() - start
    )

    payload = JobResultOut(
        id=job.id,
        status=job.status.value,
        result=job.result if job.status == JobStatus.succeeded else None,
        error=job.error if job.status == JobStatus.failed else None,
        last_error=job.last_error,
        last_error_at=job.last_error_at,
        failed_at=job.failed_at,
        succeeded_at=job.succeeded_at,
    )

    if job.status in (JobStatus.queued, JobStatus.running):
        now = datetime.now(timezone.utc)
        if job.run_after:
            delta = (job.run_after - now).total_seconds()
            retry_after_seconds = str(max(1, int(delta + 0.999)))  # ceil-ish
        else:
            retry_after_seconds = "1"
        return JSONResponse(
            status_code=202,
            content=jsonable_encoder(payload),
            headers={
                "Retry-After": str(retry_after_seconds),
                "Cache-Control": "no-store",
            },
        )

    return JSONResponse(status_code=200, content=jsonable_encoder(payload))

@router.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(
        content=data,
        media_type=CONTENT_TYPE_LATEST
    )