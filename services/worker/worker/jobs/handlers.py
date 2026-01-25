import asyncio
from worker.models.job import Job

async def handle_csv_summary(job: Job) -> dict:
    await asyncio.sleep(0.2)
    file_name = job.payload.get("file", "unknown.csv")
    return { "message": "csv_summary completed", "file": file_name, "rows": 0 }

async def handle_always_fail(job: Job) -> dict:
    raise RuntimeError("Intentional failure for retry testing")