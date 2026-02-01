from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel

class JobResultOut(BaseModel):
    id: uuid.UUID
    status: str
    result: dict | None = None
    error: str | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None
    failed_at: datetime | None = None
    succeeded_at: datetime | None = None