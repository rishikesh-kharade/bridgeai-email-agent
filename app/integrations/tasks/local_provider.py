import threading
from app.schemas.task import Task, TaskCreate


class InMemoryTaskProvider:
    """Development adapter only. Client production tasks remain client-owned."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def get_task(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks.get(str(task_id))

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())

    def find_existing_task(self, email_id: str, title: str) -> Task | None:
        normalized = " ".join(title.lower().split())
        with self._lock:
            for task in self._tasks.values():
                if task.source_email_id == str(email_id) and " ".join(task.title.lower().split()) == normalized:
                    return task
        return None

    def create_task(self, task: TaskCreate) -> Task:
        with self._lock:
            task_id = str(len(self._tasks) + 1)
            created = Task(id=task_id, **task.model_dump())
            self._tasks[task_id] = created
            return created

    def create_task_if_absent(self, task: TaskCreate) -> tuple[Task, bool]:
        normalized = " ".join(task.title.lower().split())
        with self._lock:
            for existing in self._tasks.values():
                if (existing.source_email_id == task.source_email_id
                        and " ".join(existing.title.lower().split()) == normalized):
                    return existing, False
            task_id = str(len(self._tasks) + 1)
            created = Task(id=task_id, **task.model_dump())
            self._tasks[task_id] = created
            return created, True

    def get_task_count(self) -> int:
        return len(self.list_tasks())
