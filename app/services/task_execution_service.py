import re
from app.integrations.tasks.provider import TaskProvider
from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task import TaskCreate
from app.schemas.task_execution import ActionItemTaskResult, TaskExecutionResult
from app.services.task_decision_service import decide_task_creation


def normalize_task_title(title: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", title.lower()))


def create_tasks_if_needed(
    provider: TaskProvider,
    *,
    email_id: str,
    subject: str,
    analysis: AIAnalysis,
) -> TaskExecutionResult:
    decision = decide_task_creation(analysis)
    if not decision.should_create_task:
        return TaskExecutionResult(
            decision=decision,
            task_created=False,
            task_results=[],
            message="No task was created.",
        )

    results: list[ActionItemTaskResult] = []
    for action_item in analysis.action_items:
        normalized = normalize_task_title(action_item)
        if not normalized:
            results.append(ActionItemTaskResult(
                title=action_item,
                task_created=False,
                message="No task was created because this action item is empty.",
            ))
            continue

        task_data = TaskCreate(
            source_email_id=str(email_id),
            title=action_item,
            description=(
                f"Source email subject: {subject}\n\n"
                f"AI summary:\n{analysis.summary}\n\n"
                f"Action item:\n{action_item}"
            ),
            priority=analysis.priority.lower(),
        )
        created, was_created = provider.create_task_if_absent(task_data)
        results.append(ActionItemTaskResult(
            title=action_item,
            task_created=was_created,
            task_id=created.id,
            message=("Task created after deterministic business-rule approval." if was_created
                     else "No task was created because this action item already exists for this email."),
        ))

    count = sum(result.task_created for result in results)
    return TaskExecutionResult(
        decision=decision,
        task_created=count > 0,
        task_results=results,
        message=f"{count} task(s) created from this email.",
    )
