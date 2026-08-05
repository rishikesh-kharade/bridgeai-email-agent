from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
    )

    return user_repository.create_user(db, db_user)

def get_users(db: Session):
    return user_repository.get_users(db)

def get_user_by_id(db: Session, user_id: int):
    return user_repository.get_user_by_id(db, user_id)

def update_user(db: Session, user: User, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    return user_repository.update_user(db, user)

def delete_user(db: Session, user: User):
    return  user_repository.delete_user(db, user)