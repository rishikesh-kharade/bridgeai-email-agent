from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings


def build_router(email_provider):
    router = APIRouter(prefix="/emails", tags=["emails"])

    @router.get("")
    def list_emails(limit: int = Query(default=settings.default_email_list_limit, ge=1, le=settings.max_email_list_limit)):
        return email_provider.list_emails(limit)

    @router.get("/{email_id}")
    def get_email(email_id: str):
        email = email_provider.get_email(email_id)
        if email is None:
            raise HTTPException(status_code=404, detail="Email not found")
        return email

    return router
