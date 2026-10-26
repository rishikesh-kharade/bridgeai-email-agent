"""Read-only Google Calendar adapter for the local user's upcoming events."""
from datetime import datetime, timedelta, timezone

from app.integrations.google.oauth import GoogleOAuthError, GoogleOAuthManager
from app.schemas.meeting import Meeting


class GoogleCalendarProviderError(RuntimeError):
    """Safe application-level Google Calendar error."""


class GoogleCalendarProvider:
    def __init__(self, service_factory):
        self._service_factory = service_factory
        self._service = None

    @property
    def _api(self):
        if self._service is None:
            try:
                self._service = self._service_factory()
            except GoogleOAuthError as exc:
                raise GoogleCalendarProviderError(str(exc)) from exc
            except Exception as exc:
                raise GoogleCalendarProviderError("Google Calendar authorization is unavailable.") from exc
        return self._service

    @classmethod
    def from_settings(cls, settings, oauth_manager: GoogleOAuthManager | None = None):
        manager = oauth_manager or GoogleOAuthManager(settings)
        return cls(service_factory=lambda: manager.service("calendar", "v3"))

    def list_upcoming_meetings(self, limit: int = 20) -> list[Meeting]:
        if not 1 <= limit <= 50:
            raise ValueError("Meeting limit must be between 1 and 50.")
        now = datetime.now(timezone.utc)
        try:
            result = self._api.events().list(
                calendarId="primary",
                timeMin=now.isoformat().replace("+00:00", "Z"),
                timeMax=(now + timedelta(days=14)).isoformat().replace("+00:00", "Z"),
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            meetings = []
            for event in result.get("items", []):
                event_id = event.get("id")
                event_start = event.get("start") or {}
                start = event_start.get("dateTime") or event_start.get("date")
                if not event_id or not start:
                    continue
                event_end = event.get("end") or {}
                end = event_end.get("dateTime") or event_end.get("date")
                meetings.append(Meeting(
                    id=event_id,
                    title=(event.get("summary") or "Busy")[:300],
                    start=start,
                    end=end,
                    all_day="date" in event_start and "dateTime" not in event_start,
                    location=event.get("location"),
                    url=event.get("htmlLink"),
                ))
            return meetings
        except GoogleCalendarProviderError:
            raise
        except Exception as exc:
            raise GoogleCalendarProviderError("Google Calendar event listing failed.") from exc
