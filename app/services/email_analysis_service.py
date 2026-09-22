from sqlalchemy.orm import Session

from app.models.email_analysis import EmailAnalysis as EmailAnalysisModel, EmailAnalysis
from app.repositories import email_analysis_repository
from app.schemas.ai_analysis import AIAnalysis

MODEL_NAME = "gemini-3.6-flash"
PROMPT_VERSION = "v1"


def save_email_analysis(
    db: Session,
        *,
    email_id: int,
        analysis: AIAnalysis,
) -> EmailAnalysisModel:
    """
    Save the AI result for audit/history.

    This does not make business decisions and does not create tasks.
    """

    db_analysis = EmailAnalysisModel(
        email_id=email_id,
        summary=analysis.summary,
        category=analysis.category.model_dump_json(),
        priority=analysis.priority,
        sentiment=analysis.sentiment,
        requires_action=analysis.requires_action,
        requires_attention=analysis.requires_attention,
        action_items=analysis.action_items,
        model_names=MODEL_NAME,
        Prompt_version=PROMPT_VERSION,
    )

    return email_analysis_repository.create_email_analysis(db, db_analysis,)

def get_analysis_by_email_id(
    db: Session,
        email_id: int,
)->list[EmailAnalysisModel]:
    return email_analysis_repository.get_analyses_by_email_id(
        db, email_id,
    )