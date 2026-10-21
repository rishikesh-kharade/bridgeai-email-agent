from typing import Literal, TypedDict

from app.schemas.ai_analysis import AIAnalysis


class EmailAgentState(TypedDict, total=False):
    message: str
    intent: Literal["list", "retrieve", "summary", "analyze", "question", "tasks", "unknown"]
    requested_task: bool
    email_id: str | None
    email_limit: int
    email: object
    analysis: AIAnalysis
    response: str
    current_email_id: str | None

__all__ = ["EmailAgentState"]
