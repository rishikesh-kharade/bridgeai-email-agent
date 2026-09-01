from langchain_core.tools import tool

from app.db.database import SessionLocal
from app.services import user_service, task_service


@tool
def get_task_count(user_name:str) -> str:
    """Get the number of tasks assigned to a user."""

    db = SessionLocal()

    try:
        user = user_service.get_user_by_name(db, user_name)

        if not user:
            return f"User {user_name} was not found."

        count = task_service.get_task_count(db, user.id)

        return f"{user_name} has {count} tasks."

    finally:
        db.close()