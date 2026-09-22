from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories import task_repository
from app.schemas.task import TaskCreate


def create_task(db: Session, task: TaskCreate):
    db_task = Task(
        email_id=task.email_id,
        assigned_to_id=task.assigned_to_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
    )

    return task_repository.create_task(db, db_task)


def get_task_count(db: Session, user_id: int):
    return task_repository.get_task_count(db,user_id)


def get_task_by_email_id(db: Session, email_id: int):
    return task_repository.get_task_by_email_id(db, email_id)

def get_tasks_by_email_id(db: Session, email_id: int):
    return task_repository.get_tasks_by_email_id(db, email_id)


