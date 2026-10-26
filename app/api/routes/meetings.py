from fastapi import APIRouter, HTTPException, Query


def build_router(calendar_provider):
    router = APIRouter(prefix="/meetings", tags=["meetings"])

    @router.get("")
    def list_upcoming_meetings(limit: int = Query(default=20, ge=1, le=50)):
        if calendar_provider is None:
            raise HTTPException(status_code=503, detail="Google Calendar is not enabled.")
        return calendar_provider.list_upcoming_meetings(limit)

    return router
