import re

from sqlalchemy.orm import Session

from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task import TaskCreate
from app.schemas.task_execution import TaskExecutionResult, ActionItemTaskResult
from app.services import task_service
from app.services.task_decision_service import decide_task_creation


def normalize_task_title(title: str) -> str:
    """
    Compare titles without differences in letter case or punctuation.

    Example:
    'Fix Payment API 500 Error!'
    and
    'fix payment api 500 error!'
    become the same value.
    """

    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(words)


def create_tasks_if_needed(
        db: Session,
        *,
        email_id: int,
        assigned_to_id: int,
        subject: str,
        analysis: AIAnalysis,
) -> TaskExecutionResult:
    """
    Create one task per unique action item for onw email.

    The same email cannot create the same action-item task twice.
    Different emails may create similar tasks for now.
    """

    decision = decide_task_creation(analysis)

    if not decision.should_create_task:
        return TaskExecutionResult(
            decision=decision,
            task_created=False,
            task_results=[],
            message="No task was created because the business rules did not approve it.",
        )

    action_items = analysis.action_items or [
        f"Review and take action on: {subject}"
    ]

    existing_tasks = task_service.get_tasks_by_email_id(db, email_id)

    existing_task_titles = {
        normalize_task_title(task.title)
        for task in existing_tasks
    }

    task_results = []

    for action_item in action_items:
        normalized_title = normalize_task_title(action_item)

        if normalized_title in existing_task_titles:
            task_results.append(
                ActionItemTaskResult(
                    title=action_item,
                    task_created=False,
                    message=(
                        "No task was created because this action item already "
                        "exists for this email."
                    ),
                )
            )
            continue

        task = TaskCreate(
            email_id=email_id,
            assigned_to_id=assigned_to_id,
            title=action_item,
            description=(
                f"Source email subject: {subject}\n\n"
                f"AI summary:\n{analysis.summary}\n\n"
                f"Action item:\n{action_item}"
            ),
            priority=analysis.priority.lower(),
        )

        created_task = task_service.create_task(db, task)

        task_results.append(
            ActionItemTaskResult(
                title=action_item,
                task_created=True,
                task_id=created_task.id,
                message="Task created after deterministic business-rule approval.",
            )
        )

        existing_task_titles.add(normalized_title)

    created_count = sum(
        result.task_created for result in task_results
    )


    return TaskExecutionResult(
        decision=decision,
        task_created=created_count > 0,
        task_results=task_results,
        message=f"{created_count} task(s) created from this email.",
    )