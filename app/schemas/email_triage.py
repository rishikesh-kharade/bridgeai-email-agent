from typing import Literal

from pydantic import BaseModel, Field


class EmailTriageItem(BaseModel):
    index: int = Field(ge=1, le=20)
    summary: str = Field(min_length=1, max_length=600)
    priority: Literal["Critical", "High", "Medium", "Low"]
    requires_action: bool
    requires_attention: bool
    action_items: list[str] = Field(default_factory=list, max_length=10)


class EmailTriageResult(BaseModel):
    emails: list[EmailTriageItem] = Field(default_factory=list, max_length=20)
