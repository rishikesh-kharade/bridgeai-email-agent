from sqlalchemy.orm import Session


from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task import TaskCreate
from app.schemas.task_execution import TaskExecutionResult
from app.services import task_service
from app.services.task_decision_service import decide_task_creation


def create_task_if_needed(
        db: Session,
        *,
        email_id: int,
        assigned_to_id: int,
        subject: str,
        description: str,
        analysis: AIAnalysis,
) -> TaskExecutionResult:
    """
    Controlled task-creation workflow.

    The LLM does not call this function. It only runs in backend code after
    deterministic business rules approve task creation.
    """

    decision = decide_task_creation(analysis)

    if not decision.should_create_task:
        return TaskExecutionResult(
            decision=decision,
            task_created=False,
            message="No task was created because the business rules did not approve it.",
        )

    existing_task = task_service.get_task_by_email_id(db, email_id)

    if existing_task:
        return TaskExecutionResult(
            decision=decision,
            task_created=False,
            task_id=existing_task.id,
            message="No task was created because this email already has a task.",
        )

    action_items = "\n".join(
        f"-{item}" for item in analysis.action_items
    ) or "-Review the email and take the necessary action."

    task = TaskCreate(
        email_id=email_id,
        assigned_to_id=assigned_to_id,
        title=subject,
        description=(
            f"AI summary:\n{analysis.summary}\n\n"
            f"Action items:\n{action_items}"
        ),
        priority=analysis.priority.lower(),
    )

    created_task = task_service.create_task(db, task)

    return TaskExecutionResult(
        decision=decision,
        task_created=True,
        task_id=created_task.id,
        message="Task created after deterministic business-rule approval.",
    )