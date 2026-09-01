from app.schemas.ai_analysis import AIAnalysis
from app.schemas.task_decision import TaskCreationDecision



TASK_CREATING_PRIORITIES = {"Critical", "High"}

def decide_task_creation(analysis: AIAnalysis) -> TaskCreationDecision:
    """
    Apply BridgeAI business rules to an AI analysis.

    This function is deterministic: the same AIAnalysis always produces
    the same decision. It does not create database records or tasks.
    """

    if not analysis.requires_action:
        return TaskCreationDecision(
            should_create_task=False,
            reason= "No task created because the email does not require action.",
                     )

    if analysis.priority in TASK_CREATING_PRIORITIES:
        return TaskCreationDecision(
            should_create_task=True,
            reason=(
                f"Task created because the email requires action ans has"
                f"{analysis.priority} priority."
            ),
            recommended_priority= analysis.priority,
        )


    if analysis.priority == "Medium" and analysis.requires_action:
        return TaskCreationDecision(
            should_create_task=True,
            reason= (f"Task created because the email requires action and has Medium"
                     "priority, and requires attention."),
            recommended_priority= analysis.priority,
        )

    return TaskCreationDecision(
        should_create_task=False,
        reason=(
            "No task created because the email is not High/Critical and does "
            "not meet the Medium-priority attention rule."
        ),
    )