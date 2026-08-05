from sqlalchemy.orm import Session

from app.models.user import User

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def update_user(db: Session, user: User):
    db.commit()
    db.refresh(user)

    return user

def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()

def get_users(db: Session):
    users = db.query(User).all()
    return users

def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    return user


