from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routes.agent import build_router as build_agent_router
from app.api.routes.emails import build_router as build_email_router
from app.api.routes.health import router as health_router
from app.api.routes.meetings import build_router as build_meetings_router
from app.api.routes.tasks import build_router as build_task_router
from app.agents.graph import build_graph
from app.core.config import settings
from app.core.logger import log_event
from app.integrations.email.gmail_provider import GmailEmailProvider, GmailProviderError
from app.integrations.calendar.google_calendar_provider import GoogleCalendarProvider, GoogleCalendarProviderError
from app.integrations.google.oauth import GoogleOAuthManager
from app.integrations.tasks.google_tasks_provider import GoogleTasksProvider, GoogleTasksProviderError


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_event("application.started", environment=settings.environment)
    yield
    log_event("application.stopped", environment=settings.environment)


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

    @app.exception_handler(GoogleCalendarProviderError)
    async def calendar_provider_error(_request: Request, _exc: GoogleCalendarProviderError):
        return JSONResponse(status_code=503, content={"detail": "Google Calendar is unavailable or not authorized."})

    oauth = GoogleOAuthManager(settings)

    email_provider = GmailEmailProvider.from_settings(settings, oauth)
    task_provider = GoogleTasksProvider.from_settings(settings, oauth)
    calendar_provider = GoogleCalendarProvider.from_settings(settings, oauth) if settings.calendar_enabled else None

    graph = build_graph(email_provider, task_provider, calendar_provider)

    app.include_router(health_router)
    app.include_router(build_agent_router(graph))
    app.include_router(build_email_router(email_provider))
    app.include_router(build_task_router(task_provider))
    app.include_router(build_meetings_router(calendar_provider))

    static_dir = Path(__file__).parent / "static"
    react_ui_dir = static_dir / "react-ui"
    if (react_ui_dir / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=react_ui_dir / "assets"), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def home():
        react_index = react_ui_dir / "index.html"
        return FileResponse(react_index if react_index.is_file() else static_dir / "index.html")

    return app


app = create_app()
