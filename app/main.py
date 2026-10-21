from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes.agent import build_router as build_agent_router
from app.api.routes.emails import build_router as build_email_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import build_router as build_task_router
from app.agents.graph import build_graph
from app.core.config import settings
from app.core.logger import logger
from app.integrations.email.local_provider import InMemoryEmailProvider
from app.integrations.email.gmail_provider import GmailEmailProvider, GmailProviderError
from app.integrations.google.oauth import GoogleOAuthManager
from app.integrations.tasks.google_tasks_provider import GoogleTasksProvider, GoogleTasksProviderError
from app.integrations.tasks.local_provider import InMemoryTaskProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} in {settings.environment} mode")
    yield
    logger.info("Shutting down")


def create_app():
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered email intelligence and orchestration layer.",
        lifespan=lifespan,
    )

    @app.exception_handler(GmailProviderError)
    async def gmail_provider_error(_request: Request, _exc: GmailProviderError):
        return JSONResponse(status_code=503, content={"detail": "Email provider is unavailable or not authorized."})

    @app.exception_handler(GoogleTasksProviderError)
    async def task_provider_error(_request: Request, _exc: GoogleTasksProviderError):
        return JSONResponse(status_code=503, content={"detail": "Google Tasks is unavailable or not authorized."})

    oauth = GoogleOAuthManager(settings)

    if settings.provider_mode == "gmail":
        email_provider = GmailEmailProvider.from_settings(settings, oauth)
    else:
        email_provider = InMemoryEmailProvider()
    if settings.task_provider_mode == "google_tasks":
        task_provider = GoogleTasksProvider.from_settings(settings, oauth)
    else:
        task_provider = InMemoryTaskProvider()

    graph = build_graph(email_provider, task_provider)

    app.include_router(health_router)
    app.include_router(build_agent_router(graph))
    app.include_router(build_email_router(email_provider))
    app.include_router(build_task_router(task_provider))

    from fastapi.responses import FileResponse
    from pathlib import Path

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    return app


app = create_app()
