"""Command-line entry point for the per-user local web app."""
import uvicorn
from app.core.config import settings


def main():
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.app_port, reload=False)
