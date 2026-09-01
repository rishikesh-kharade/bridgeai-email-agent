from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.task import TaskResponse, TaskCreate
from app.services import task_service

router = APIRouter(
    prefix = '/tasks',
    tags=['tasks']
)

@router.post("", response_model=TaskResponse)
def  create_task(
        task: TaskCreate,
        db: Session = Depends(get_db)
):
    return task_service.create_task(db, task)