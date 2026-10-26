from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    source_email_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=10000)
    status: str = "pending"
    priority: str = "normal"


class TaskCreate(BaseModel):
    source_email_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=10000)
    status: str = "pending"
    priority: str = "normal"
