from prometheus_client import Counter, Histogram

WORKER_JOB_CLAIMED_TOTAL = Counter(
    "worker_job_claimed_total",
    "Total number of jobs claimed by the worker",
    ["job_type"]
)

WORKER_JOB_SUCCEEDED_TOTAL = Counter(
    "worker_job_succeeded_total",
    "Total number of jobs succeeded in the worker",
    ["job_type"]
)

WORKER_JOB_FAILED_TOTAL = Counter(
"worker_job_failed_total",
    "Total number of jobs permanently failed in the worker",
    ["job_type"]
)

WORKER_JOB_RETRY_SCHEDULED_TOTAL = Counter(
    "worker_job_retry_scheduled_total",
    "Total number of retries scheduled by the worker",
    ["job_type"],
)

WORKER_JOB_DURATION_SECONDS = Histogram(
    "worker_job_duration_seconds",
    "Time spent processing a job in seconds",
    ["job_type"],
)