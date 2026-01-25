from worker.models.job import Job

async def handle_csv_summary(job: Job) -> dict:
    file_name = job.payload.get("file", "unknown.csv")
    return { "message": "csv_summary completed", "file": file_name, "rows": 0 }