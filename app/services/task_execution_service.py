import re
import logging
from app.integrations.tasks.google_tasks_provider import GoogleTasksProvider
from app.core.logger import log_event
from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task import TaskCreate
from app.schemas.task_execution import ActionItemTaskResult, TaskExecutionResult
from app.services.task_decision_service import decide_task_creation


def normalize_task_title(title: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", title.lower()))


def create_tasks_if_needed(
    provider: GoogleTasksProvider,
    *,
    email_id: str,
    subject: str,
    analysis: AIAnalysis,
    task_title: str | None = None,
) -> TaskExecutionResult:
    decision = decide_task_creation(analysis)
    log_event(
        "task.decision.completed", decision=decision.reason,
        priority=analysis.priority, approved=decision.should_create_task,
    )
    if not decision.should_create_task:
        return TaskExecutionResult(
            decision=decision,
            task_created=False,
            task_results=[],
            message="No task was created.",
        )

    results: list[ActionItemTaskResult] = []
    if task_title:
        clean_title = " ".join(task_title.split())
        action_items = "\n".join(f"- {item}" for item in analysis.action_items)
        task_data = TaskCreate(
            source_email_id=str(email_id),
            title=clean_title,
            description=(
                f"Source email subject: {subject}\n\n"
                f"AI summary:\n{analysis.summary}\n\n"
                f"Action items:\n{action_items}"
            ),
            priority=analysis.priority.lower(),
        )
        created, was_created = _create_task(provider, task_data)
        result = ActionItemTaskResult(
            title=clean_title,
            task_created=was_created,
            task_id=created.id,
            message=("Task created after deterministic business-rule approval." if was_created
                     else "No task was created because this task already exists for this email."),
        )
        return TaskExecutionResult(
            decision=decision,
            task_created=was_created,
            task_results=[result],
            message=("1 task created from this email." if was_created
                     else "No task created; a task with this title already exists for this email."),
        )

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
        created, was_created = _create_task(provider, task_data)
        results.append(ActionItemTaskResult(
            title=action_item,
            task_created=was_created,
            task_id=created.id,
            message=("Task created after deterministic business-rule approval." if was_created
                     else "No task was created because this action item already exists for this email."),
        ))

    count = sum(result.task_created for result in results)
    log_event("task.execution.completed", task_created=count > 0, task_count=count)
    return TaskExecutionResult(
        decision=decision,
        task_created=count > 0,
        task_results=results,
        message=f"{count} task(s) created from this email.",
    )


def _create_task(provider: GoogleTasksProvider, task_data: TaskCreate):
    log_event("task.provider.create.started", priority=task_data.priority)
    try:
        created, was_created = provider.create_task_if_absent(task_data)
    except Exception as exc:
        log_event(
            "task.provider.create.failed", level=logging.ERROR,
            error_type=type(exc).__name__, priority=task_data.priority,
        )
        raise
    log_event("task.provider.create.completed", task_created=was_created, priority=task_data.priority)
    return created, was_created
