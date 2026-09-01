from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.email import EmailCreate, EmailUpdate
from app.services import email_service

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



@router.delete("/{email_id}")
def delete_email(email_id: int ,db: Session = Depends(get_db)):
    email = email_service.get_email_by_id(db, email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email_service.delete_email(db, email)

    return {"message": "Email deleted successfully"}



