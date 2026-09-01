

from sqlalchemy.orm import Session

from app.models.email import Email


def create_email(db: Session, email: Email):
    db.add(email)
    db.commit()
    db.refresh(email)

    return email

def get_emails(db: Session):
    return db.query(Email).all()

def update_email(db: Session, email: Email):
    db.commit()
    db.refresh(email)
    return email

def get_email_by_id(db: Session, email_id: int):
    return db.query(Email).filter(Email.id == email_id).first()

def delete_email(db: Session, email: Email):
    db.delete(email)
    db.commit()