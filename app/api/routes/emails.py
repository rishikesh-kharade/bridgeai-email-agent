import json

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.email import EmailCreate, EmailUpdate
from app.services import email_service, ai_service, email_analysis_service
from app.services.task_execution_service import create_tasks_if_needed


router = APIRouter(
    prefix="/emails",
    tags=["emails"],

)

@router.post("")
def create_email(
        email: EmailCreate,
        db: Session = Depends(get_db)
):

    try:
        return email_service.create_email(db, email)

    except IntegrityError:
        db.rollback()

        raise HTTPException(status_code=400, detail="Email already exists")


@router.get("")
def get_emails(db: Session = Depends(get_db)):
    return email_service.get_emails(db)

@router.get("/{email_id}")
def get_email_by_id(email_id: int ,db: Session = Depends(get_db)):
    email = email_service.get_email_by_id(db, email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email


@router.get("/{email_id}/analyses")
def get_email_analysis(
        email_id: int ,
        db: Session = Depends(get_db),
):
    email = email_service.get_email_by_id(db, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    analyses = email_analysis_service.get_analysis_by_email_id(
        db, email_id,
    )

    return [{
        "id": analysis.id,
        "email_id": analysis.email.id,
        "summary": analysis.summary,
        "category": json.loads(analysis.category),
        "priority": analysis.priority,
        "sentiment": analysis.sentiment,
        "requires_action": analysis.requires_action,
        "requires_attention": analysis.requires_attention,
        "action_items": analysis.action_items,
        "model_name": analysis.model_name,
        "prompt_version": analysis.prompt_version,
        "created_at": analysis.created_at,
    }
    for analysis in analyses
]

@router.patch("/{email_id}")
def update_email(
        email_id: int,
        email_update: EmailUpdate,
        db: Session = Depends(get_db)
):

    email = email_service.get_email_by_id(db, email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        return email_service.update_email(db, email, email_update)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")



@router.post("/{email_id}/process")
def process_email(
        email_id: int,
        assigned_to_id: int,
        db: Session = Depends(get_db),
):
    """
    Analyze an existing email and, only when business rules approve it,
    create one task for the selected user.
    """

    email = email_service.get_email_by_id(db, email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    analysis = ai_service.analyze_email(
        subject=email.subject,
        body=email.body,
    )

    saved_analysis = email_analysis_service.save_email_analysis(
        db, email_id=email_id, analysis=analysis
    )

    task_execution = create_tasks_if_needed(
        db=db,
        email_id=email_id,
        assigned_to_id=assigned_to_id,
        subject=email.subject,
        analysis=analysis,
    )

    return {
        "email_id": email_id,
        "analysis_id": saved_analysis.id,
        "analysis": analysis.model_dump(),
        "task_execution": task_execution.model_dump(),
    }

@router.delete("/{email_id}")
def delete_email(email_id: int ,db: Session = Depends(get_db)):
    email = email_service.get_email_by_id(db, email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_service.delete_email(db, email)

    return {"message": "Email deleted successfully"}



