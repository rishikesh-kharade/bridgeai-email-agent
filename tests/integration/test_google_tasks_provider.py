from app.integrations.tasks.google_tasks_provider import GoogleTasksProvider
from app.schemas.task import TaskCreate


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class TaskLists:
    def list(self, **_kwargs):
        return Request({"items": [{"id": "bridgeai-list", "title": "BridgeAI"}]})


class Tasks:
    def __init__(self):
        self.items = []

    def list(self, **_kwargs):
        return Request({"items": list(self.items)})

    def insert(self, *, tasklist, body):
        item = {"id": str(len(self.items) + 1), **body, "status": "needsAction"}
        self.items.append(item)
        return Request(item)

    def get(self, *, tasklist, task):
        return Request(next(item for item in self.items if item["id"] == task))


class API:
    def __init__(self):
        self.task_items = Tasks()

    def tasklists(self):
        return TaskLists()

    def tasks(self):
        return self.task_items


def test_creates_in_bridgeai_list_and_deduplicates_retries():
    api = API()
    provider = GoogleTasksProvider(lambda: api)
    task = TaskCreate(
        source_email_id="mail-123", title="Review request",
        description="Review the customer request.", priority="high",
    )
    first, created = provider.create_task_if_absent(task)
    second, retried = provider.create_task_if_absent(task)
    assert created is True
    assert retried is False
    assert second.id == first.id
    assert len(api.task_items.items) == 1
    assert second.source_email_id == "mail-123"
    assert second.priority == "high"
    assert "bridgeai-idempotency:" not in second.description


def test_task_list_does_not_trigger_creation():
    class EmptyLists(TaskLists):
        def list(self, **_kwargs):
            return Request({"items": []})

    class EmptyApi(API):
        def tasklists(self):
            return EmptyLists()

        def task_items_count(self):
            return len(self.task_items.items)

    api = EmptyApi()
    provider = GoogleTasksProvider(lambda: api)
    assert provider.list_tasks() == []
