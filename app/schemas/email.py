from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Email(BaseModel):
    id: str
    provider_message_id: str
    sender: EmailStr
    receiver: EmailStr
    subject: str
    body: str
    is_read: bool = False
    received_at: datetime | None = None
    labels: list[str] = Field(default_factory=list)


class EmailCreate(BaseModel):
    sender: EmailStr
    receiver: EmailStr
    subject: str
    body: str
    provider_message_id: str


class EmailUpdate(BaseModel):
    sender: EmailStr | None = None
    receiver: EmailStr | None = None
    subject: str | None = None
    body: str | None = None
    is_read: bool | None = None
