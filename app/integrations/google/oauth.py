"""Lazy local OAuth flow shared by Gmail and Google Tasks adapters."""
from pathlib import Path
import json
import threading


class GoogleOAuthError(RuntimeError):
    """Safe error for missing or invalid local Google authorization."""


class GoogleOAuthManager:
    def __init__(self, settings):
        self.credentials_path = Path(settings.oauth_credentials_path)
        self.token_path = Path(settings.oauth_token_path)
        self.scopes = list(settings.oauth_scopes)
        calendar_scope = "https://www.googleapis.com/auth/calendar.events.readonly"
        if settings.calendar_enabled and calendar_scope not in self.scopes:
            self.scopes.append(calendar_scope)
        self.timeout = settings.request_timeout
        self._credentials = None
        self._lock = threading.Lock()

    def credentials(self):
        if self._credentials and self._credentials.valid and self._credentials.has_scopes(self.scopes):
            return self._credentials
        with self._lock:
            if self._credentials and self._credentials.valid and self._credentials.has_scopes(self.scopes):
                return self._credentials
            self._credentials = self._authorize()
            return self._credentials

    def _authorize(self):
        if not self.credentials_path.is_file():
            raise GoogleOAuthError(f"OAuth client file not found: {self.credentials_path}")
        try:
            from google.auth.transport.requests import Request
            from google.auth.exceptions import RefreshError
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise GoogleOAuthError("Install Google OAuth dependencies from requirements.txt.") from exc
        try:
            credentials = None
            stored_scopes = None
            if self.token_path.is_file():
                try:
                    stored_scopes = json.loads(self.token_path.read_text(encoding="utf-8")).get("scopes", [])
                except (OSError, ValueError, AttributeError):
                    stored_scopes = []
                if set(self.scopes).issubset(set(stored_scopes)):
                    credentials = Credentials.from_authorized_user_file(str(self.token_path), self.scopes)
            if credentials and credentials.has_scopes(self.scopes):
                if credentials.valid:
                    return credentials
                if credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                    except RefreshError:
                        credentials = None
                else:
                    credentials = None
            if not credentials or not credentials.valid or not credentials.has_scopes(self.scopes):
                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), self.scopes)
                credentials = flow.run_local_server(port=0)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(credentials.to_json(), encoding="utf-8")
            try:
                self.token_path.chmod(0o600)
            except OSError:
                pass
            return credentials
        except GoogleOAuthError:
            raise
        except Exception as exc:
            raise GoogleOAuthError("Google authorization failed; confirm the Workspace account and requested permissions.") from exc

    def service(self, api: str, version: str):
        try:
            from google_auth_httplib2 import AuthorizedHttp
            from googleapiclient.discovery import build
            import httplib2
            http = AuthorizedHttp(self.credentials(), http=httplib2.Http(timeout=self.timeout))
            return build(api, version, http=http, cache_discovery=False)
        except GoogleOAuthError:
            raise
        except Exception as exc:
            raise GoogleOAuthError("Google service could not be initialized.") from exc
