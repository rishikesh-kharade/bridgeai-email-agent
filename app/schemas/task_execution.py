from pydantic import BaseModel

from app.schemas.task_decision import TaskCreationDecision


class TaskExecutionResult(BaseModel):
    decision: TaskCreationDecision
    task_created: bool
    task_id: int | None = None
    message: str