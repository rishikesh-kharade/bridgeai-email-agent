from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: str = Field(default="default", min_length=1, max_length=128)


class AgentChatResponse(BaseModel):
    thread_id: str
    response: str
    current_email_id: str | None = None
