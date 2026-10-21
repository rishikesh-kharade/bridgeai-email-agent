from fastapi import APIRouter


def build_router(task_provider):
    router = APIRouter(prefix="/tasks", tags=["tasks"])

    @router.get("")
    def list_tasks():
        return task_provider.list_tasks()

    return router
