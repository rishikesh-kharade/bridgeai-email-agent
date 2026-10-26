from pathlib import Path
import pytest

from app.integrations.google.oauth import GoogleOAuthError, GoogleOAuthManager
from app.core.config import Settings


def test_oauth_is_lazy_and_reports_missing_client_safely():
    settings = Settings(oauth_credentials_path="credentials/does-not-exist.json",
                        oauth_token_path=".oauth-test-token.json")
    manager = GoogleOAuthManager(settings)
    assert manager._credentials is None
    with pytest.raises(GoogleOAuthError, match="OAuth client file not found"):
        manager.credentials()
    assert not Path(settings.oauth_token_path).exists()


def test_calendar_readonly_scope_is_requested_only_when_calendar_is_enabled():
    base = GoogleOAuthManager(Settings(calendar_enabled=False))
    calendar = GoogleOAuthManager(Settings(calendar_enabled=True))
    scope = "https://www.googleapis.com/auth/calendar.events.readonly"
    assert scope not in base.scopes
    assert scope in calendar.scopes
