"""In-memory fakes used only by automated tests."""

import threading

from app.schemas.email import Email
from app.schemas.meeting import Meeting
from app.schemas.task import Task, TaskCreate


class FakeEmailProvider:
    def __init__(self, emails: list[Email] | None = None):
        self._emails = {email.id: email for email in (emails or [])}

    def get_email(self, email_id: str) -> Email | None:
        return self._emails.get(str(email_id))

    def list_emails(self, limit: int = 50) -> list[Email]:
        return list(self._emails.values())[:limit]

    def search_emails(self, query: str, limit: int = 10, *, sender_only: bool = False) -> list[Email]:
        terms = [term.casefold() for term in query.split() if term]
        if not terms or not 1 <= limit <= 500:
            raise ValueError("Invalid fake email search query or limit.")
        matches = []
        for email in self._emails.values():
            searchable = str(email.sender) if sender_only else " ".join(
                (str(email.sender), str(email.receiver), email.subject, email.body)
            )
            if all(term in searchable.casefold() for term in terms):
                matches.append(email)
        return matches[:limit]

    def list_filtered_emails(self, filter_id: str, limit: int = 20) -> list[Email]:
        if filter_id == "unread":
            matches = [email for email in self._emails.values() if not email.is_read]
        elif filter_id == "important_unread":
            matches = [email for email in self._emails.values()
                       if not email.is_read and any(label.casefold() == "important" for label in email.labels)]
        else:
            raise ValueError("Unsupported fake email filter.")
        return matches[:limit]


class FakeTaskProvider:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return list(self._tasks.values())

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


class FakeCalendarProvider:
    def __init__(self, meetings: list[Meeting] | None = None):
        self._meetings = list(meetings or [])

    def list_upcoming_meetings(self, limit: int = 20) -> list[Meeting]:
        if not 1 <= limit <= 50:
            raise ValueError("Meeting limit must be between 1 and 50.")
        return self._meetings[:limit]
