import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class JobCreate(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    payload: dict = Field(default_factory=dict)
    result: dict | None = None

class JobOut(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict
    status: str
    result: dict | None = None
    error: str | None = None

    # lifecycle timestamps
    created_at: datetime
    updated_at: datetime | None = None
    started_at: datetime | None = None
    succeeded_at: datetime | None = None
    failed_at: datetime | None = None

    # retries
    attempts: int
    max_attempts: int
    run_after: datetime | None

    # last failure details
    last_error: str | None = None
    last_error_at: datetime | None = None

    # idempotency key
    idempotency_key: str | None = None

    class Config:
        from_attributes = True

class JobResultOut(BaseModel):
    """
    from GET /jobs/{id}/result
    """
    id: uuid.UUID
    status: str

    result: dict | None = None

    error: str | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None
    failed_at: datetime | None = None