from pydantic import BaseModel, EmailStr


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