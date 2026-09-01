from datetime import datetime

from pydantic import BaseModel

class TaskCreate(BaseModel):
    email_id: int
    assigned_to_id: int
    title: str
    description: str
    status: str = "pending"
    priority: str = "normal"

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None

class TaskResponse(BaseModel):
    id: int
    email_id: int
    assigned_to_id: int
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime | None = None

class Config:
    from_attributes = True