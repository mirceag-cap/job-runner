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
    attempts: int
    max_attempts: int
    run_after: datetime | None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True