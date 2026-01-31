from prometheus_client import Counter, Histogram

JOB_CREATED_TOTAL = Counter(
    "job_created_total",
    "Total number of jobs created via the API",
    ["job_type"]
)

JOB_GET_TOTAL = Counter(
    "job_get_total",
    "Total number of job GETs via the API",
)

API_REQUEST_DURATION_SECONDS = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "path"]
)