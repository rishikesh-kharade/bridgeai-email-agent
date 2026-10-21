from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task_decision import TaskCreationDecision


def decide_task_creation(analysis: AIAnalysis) -> TaskCreationDecision:
    if not analysis.requires_action:
        return TaskCreationDecision(
            should_create_task=False,
            reason="No task created because the email does not require action.",
        )

    if not analysis.action_items:
        return TaskCreationDecision(
            should_create_task=False,
            reason="No task created because the analysis contains no validated action items.",
        )

    if analysis.priority in {"Critical", "High"}:
        return TaskCreationDecision(
            should_create_task=True,
            reason=f"Task creation approved because the email requires action and has {analysis.priority} priority.",
            recommended_priority=analysis.priority,
        )

    if analysis.priority == "Medium" and analysis.requires_attention:
        return TaskCreationDecision(
            should_create_task=True,
            reason="Task creation approved because the email requires action, is Medium priority, and requires attention.",
            recommended_priority="Medium",
        )

    return TaskCreationDecision(
        should_create_task=False,
        reason="No task created because the email does not meet the task-creation rules.",
    )
