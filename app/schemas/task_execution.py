from pydantic import BaseModel
from app.schemas.task_decision import TaskCreationDecision


class ActionItemTaskResult(BaseModel):
    title: str
    task_created: bool
    task_id: str | None = None
    message: str


class TaskExecutionResult(BaseModel):
    decision: TaskCreationDecision
    task_created: bool
    task_results: list[ActionItemTaskResult]
    message: str
