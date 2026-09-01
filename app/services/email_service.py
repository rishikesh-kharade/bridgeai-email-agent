from sqlalchemy.orm import Session

from app.models.email import Email
from app.repositories import email_repository
from app.schemas.email import EmailCreate, EmailUpdate


def create_email(db: Session, email: EmailCreate):
    db_email = Email(
        provider_message_id=email.provider_message_id,
        sender=email.sender,
        receiver=email.receiver,
        subject=email.subject,
        body=email.body
    )
    return email_repository.create_email(db, db_email)

def get_emails(db: Session):
    return email_repository.get_emails(db)

def get_email_by_id(db: Session, email_id: int):
    return email_repository.get_email_by_id(db, email_id)

def update_email(db: Session, email: Email, email_update: EmailUpdate):
    update_data = email_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(email, field, value)
    return email_repository.update_email(db, email)

def delete_email(db: Session, email: Email):
    return email_repository.delete_email(db, email)


