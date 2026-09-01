from typing import Literal

from pydantic import BaseModel


class TaskCreationDecision(BaseModel):
    should_create_task: bool
    reason: str
    recommended_priority: Literal["Critical", "High", "Medium", "Low"] | None = None
