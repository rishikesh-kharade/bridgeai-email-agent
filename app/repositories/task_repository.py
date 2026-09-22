from sqlalchemy.orm import Session

from app.models.task import Task

def create_task(db: Session, task: Task):
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

def get_task_count(db: Session, user_id: int):
    return db.query(Task).filter(Task.assigned_to_id == user_id).count()

def get_task_by_email_id(db: Session, email_id: int):
    return db.query(Task).filter(Task.email_id == email_id).first()

def get_tasks_by_email_id(db: Session, email_id: int):
    return db.query(Task).filter(Task.email_id == email_id).all()


