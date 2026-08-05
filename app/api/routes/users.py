from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("")
def create_user(
        user: UserCreate,
        db: Session = Depends(get_db)
):

    try:
        return user_service.create_user(db, user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email already exists",
        )


@router.get("")
def get_users(db: Session = Depends(get_db)):
    return user_service.get_users(db)


@router.get("{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):

    user = user_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.patch("{user_id}")
def update_user(
        user_id: int,
        user_update: UserUpdate,
        db: Session = Depends(get_db)
):
    user = user_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    try:
       return user_service.update_user(db, user, user_update)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email already exists",
        )

@router.delete("/users/{user_id}")
def delete_user(
        user_id: int,
        db: Session = Depends(get_db)
):
    user = user_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user_service.delete_user(db, user)

    return {"message": "User deleted successfully"}