from langchain_core.tools import tool

from app.schemas.ai_analysis import AIAnalysis
from app.services.ai_service import analyze_email
from app.services.task_decision_service import decide_task_creation



@tool
def analyze_email_tool(subject: str, body: str) -> str:
    """Analyze an email and return its summary, category, priority,
    sentiment, attention requirement, and action items."""

    result = analyze_email(subject, body)

    return result.model_dump_json()

@tool
def decide_task_creation_tool(analysis_json: str) -> str:
    """Decide deterministically whether an analyzed email should result in a task.

    Pass the JSON returned by analyze_email_tool. This tool only makes a
    decision; it never created a task or changes the database.
    """

    analysis = AIAnalysis.model_validate_json(analysis_json)
    decision = decide_task_creation(analysis)

    return decision.model_dump_json()