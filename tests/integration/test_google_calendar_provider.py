import pytest

from app.integrations.calendar.google_calendar_provider import (
    GoogleCalendarProvider,
    GoogleCalendarProviderError,
)


class Request:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def execute(self):
        if self.error:
            raise self.error
        return self.result


class Events:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.kwargs = None

    def list(self, **kwargs):
        self.kwargs = kwargs
        return Request(self.result, self.error)


class Service:
    def __init__(self, events):
        self._events = events

    def events(self):
        return self._events


def test_lists_timed_and_all_day_events_with_bounded_window():
    events = Events({"items": [
        {"id": "timed", "summary": "Planning", "start": {"dateTime": "2026-10-25T09:30:00+05:30"},
         "end": {"dateTime": "2026-10-25T10:00:00+05:30"}, "htmlLink": "https://calendar.google.com/event"},
        {"id": "all-day", "start": {"date": "2026-10-26"}, "end": {"date": "2026-10-27"}},
        {"summary": "Missing ID", "start": {"date": "2026-10-27"}},
    ]})
    provider = GoogleCalendarProvider(lambda: Service(events))

    meetings = provider.list_upcoming_meetings(12)

    assert [meeting.id for meeting in meetings] == ["timed", "all-day"]
    assert meetings[0].title == "Planning"
    assert meetings[0].start == "2026-10-25T09:30:00+05:30"
    assert meetings[0].url == "https://calendar.google.com/event"
    assert meetings[1].title == "Busy"
    assert meetings[1].all_day is True
    assert events.kwargs["calendarId"] == "primary"
    assert events.kwargs["singleEvents"] is True
    assert events.kwargs["orderBy"] == "startTime"
    assert events.kwargs["maxResults"] == 12


def test_rejects_invalid_result_limit():
    provider = GoogleCalendarProvider(lambda: Service(Events({"items": []})))
    with pytest.raises(ValueError, match="between 1 and 50"):
        provider.list_upcoming_meetings(0)


def test_sanitizes_calendar_api_errors():
    provider = GoogleCalendarProvider(lambda: Service(Events(error=RuntimeError("private event data"))))
    with pytest.raises(GoogleCalendarProviderError, match="event listing failed") as error:
        provider.list_upcoming_meetings()
    assert "private event data" not in str(error.value)
