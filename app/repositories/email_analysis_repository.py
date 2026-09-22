from sqlalchemy.orm import Session

from app.models.email_analysis import EmailAnalysis

def create_email_analysis(db: Session, email_analysis: EmailAnalysis) -> EmailAnalysis:
    db.add(email_analysis)
    db.commit()
    db.refresh(email_analysis)

    return email_analysis

def get_analyses_by_email_id(db: Session, email_id: int) -> list[EmailAnalysis]:
    return (
        db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email_id).order_by(EmailAnalysis.created_at.desc()).all()
    )

