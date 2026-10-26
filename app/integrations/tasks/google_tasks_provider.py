"""Personal Google Tasks adapter used by a single user's local app instance."""
import hashlib
import re
import threading

from app.integrations.google.oauth import GoogleOAuthError, GoogleOAuthManager
from app.schemas.task import Task, TaskCreate


class GoogleTasksProviderError(RuntimeError):
    """Safe application-level Google Tasks error."""


class GoogleTasksProvider:
    LIST_TITLE = "BridgeAI"

    def __init__(self, service_factory):
        self._service_factory = service_factory
        self._service = None
        self._tasklist_id = None
        self._lock = threading.Lock()

    @property
    def _api(self):
        if self._service is None:
            try:
                self._service = self._service_factory()
            except GoogleOAuthError as exc:
                raise GoogleTasksProviderError(str(exc)) from exc
            except Exception as exc:
                raise GoogleTasksProviderError("Google Tasks authorization is unavailable.") from exc
        return self._service

    @classmethod
    def from_settings(cls, settings, oauth_manager: GoogleOAuthManager | None = None):
        manager = oauth_manager or GoogleOAuthManager(settings)
        return cls(service_factory=lambda: manager.service("tasks", "v1"))

    def _tasklist(self, create: bool = False) -> str | None:
        if self._tasklist_id:
            return self._tasklist_id
        try:
            token = None
            while True:
                page = self._api.tasklists().list(maxResults=100, pageToken=token).execute()
                found = next((item for item in page.get("items", []) if item.get("title") == self.LIST_TITLE), None)
                if found:
                    self._tasklist_id = found["id"]
                    return self._tasklist_id
                token = page.get("nextPageToken")
                if not token:
                    break
            if not create:
                return None
            created = self._api.tasklists().insert(body={"title": self.LIST_TITLE}).execute()
            self._tasklist_id = created["id"]
            return self._tasklist_id
        except Exception as exc:
            raise GoogleTasksProviderError("Google Tasks list could not be loaded.") from exc

    @staticmethod
    def _marker(task: TaskCreate) -> str:
        key = f"{task.source_email_id or ''}\n{' '.join(task.title.lower().split())}"
        return "bridgeai-idempotency:" + hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _map(raw: dict) -> Task:
        notes = raw.get("notes") or ""
        source_match = re.search(r"(?m)^BridgeAI source email: (.+)$", notes)
        priority_match = re.search(r"(?m)^BridgeAI priority: (.+)$", notes)
        description = re.sub(r"(?im)^(?:BridgeAI (?:source email|priority)|bridgeai-idempotency):\s*.*\n?", "", notes).strip()
        return Task(
            id=raw["id"],
            source_email_id=source_match.group(1) if source_match else None,
            title=raw.get("title", "(untitled task)"),
            description=description or "Created in Google Tasks.",
            status="completed" if raw.get("status") == "completed" else "pending",
            priority=priority_match.group(1) if priority_match else "normal",
        )

    def _all_raw_tasks(self, tasklist_id: str):
        token = None
        while True:
            page = self._api.tasks().list(
                tasklist=tasklist_id, maxResults=100, showCompleted=True, showHidden=True,
                pageToken=token,
            ).execute()
            yield from page.get("items", [])
            token = page.get("nextPageToken")
            if not token:
                break

    def list_tasks(self) -> list[Task]:
        tasklist_id = self._tasklist()
        if not tasklist_id:
            return []
        try:
            return [self._map(raw) for raw in self._all_raw_tasks(tasklist_id)]
        except Exception as exc:
            raise GoogleTasksProviderError("Google Tasks could not be listed.") from exc

    def create_task_if_absent(self, task: TaskCreate) -> tuple[Task, bool]:
        with self._lock:
            tasklist_id = self._tasklist(create=True)
            marker = self._marker(task)
            try:
                for raw in self._all_raw_tasks(tasklist_id):
                    if marker in raw.get("notes", ""):
                        return self._map(raw), False
                notes = "\n".join(part for part in (
                    task.description,
                    f"BridgeAI source email: {task.source_email_id}" if task.source_email_id else "",
                    f"BridgeAI priority: {task.priority}",
                    marker,
                ) if part)
                raw = self._api.tasks().insert(
                    tasklist=tasklist_id,
                    body={"title": task.title, "notes": notes},
                ).execute()
                return self._map(raw), True
            except GoogleTasksProviderError:
                raise
            except Exception as exc:
                raise GoogleTasksProviderError("Google Task could not be created.") from exc
