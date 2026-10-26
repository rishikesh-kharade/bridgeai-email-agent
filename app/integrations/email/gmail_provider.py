"""Read-only Gmail access for the local single-user application."""
import base64
from datetime import datetime, timezone
from email.utils import getaddresses
from app.integrations.google.oauth import GoogleOAuthManager
from app.schemas.email import Email


class GmailProviderError(RuntimeError):
    """Safe, application-level Gmail integration error."""


class GmailAuthorizationError(GmailProviderError):
    """The OAuth principal is not authorized to access the mailbox or scope."""


class GmailEmailProvider:
    FILTER_QUERIES = {
        "important_unread": "is:unread is:important to:me",
        "unread": "is:unread",
    }

    def __init__(self, service=None, service_factory=None):
        self._service = service
        self._service_factory = service_factory

    @property
    def _gmail(self):
        if self._service is None:
            try:
                self._service = self._service_factory()
            except Exception as exc:
                raise GmailProviderError("Google authorization or Gmail service initialization failed.") from exc
        return self._service

    @classmethod
    def from_settings(cls, settings, oauth_manager: GoogleOAuthManager | None = None):
        manager = oauth_manager or GoogleOAuthManager(settings)
        return cls(service_factory=lambda: manager.service("gmail", "v1"))

    @staticmethod
    def _decode_data(data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            return ""

    @classmethod
    def _body(cls, payload: dict) -> str:
        parts = payload.get("parts") or []
        plain = []
        html = []
        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            plain.append(cls._decode_data(payload["body"]["data"]))
        elif payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
            html.append(cls._decode_data(payload["body"]["data"]))
        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                nested = cls._body(part)
                if nested:
                    plain.append(nested)
            elif part.get("mimeType") in {"text/plain", "text/html"} and part.get("body", {}).get("data"):
                dest = plain if part["mimeType"] == "text/plain" else html
                dest.append(cls._decode_data(part["body"]["data"]))
        return "\n".join(plain or html)

    @classmethod
    def map_message(cls, raw: dict) -> Email:
        message_id = raw.get("id")
        if not message_id or not isinstance(raw.get("payload"), dict):
            raise GmailProviderError("Gmail returned a malformed message without an ID or payload.")
        headers = {str(h.get("name", "")).lower(): str(h.get("value", ""))
                   for h in raw["payload"].get("headers", []) if isinstance(h, dict)}
        sender = getaddresses([headers.get("from", "")])[0][1]
        recipients = getaddresses([headers.get("to", "")])
        receiver = recipients[0][1] if recipients else sender
        if not sender or not receiver:
            raise GmailProviderError("Gmail message is missing a valid sender or recipient.")
        labels = raw.get("labelIds", [])
        internal_date = raw.get("internalDate")
        try:
            received_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc) if internal_date else None
        except (ValueError, TypeError, OSError):
            received_at = None
        return Email(id=message_id, provider_message_id=message_id, sender=sender,
                     receiver=receiver, subject=headers.get("subject", "(no subject)"),
                     body=cls._body(raw["payload"]), is_read="UNREAD" not in labels,
                     received_at=received_at, labels=labels)

    def get_email(self, email_id: str) -> Email | None:
        try:
            raw = self._gmail.users().messages().get(userId="me", id=str(email_id), format="full").execute()
        except GmailProviderError:
            raise
        except Exception as exc:
            if getattr(exc, "resp", None) is not None and getattr(exc.resp, "status", None) == 404:
                return None
            if getattr(exc, "resp", None) is not None and getattr(exc.resp, "status", None) == 403:
                raise GmailAuthorizationError("Gmail access is denied; check the authorized Workspace account and read-only scope.") from exc
            raise GmailProviderError("Gmail message retrieval failed.") from exc
        return self.map_message(raw)

    def list_emails(self, limit: int = 50, *, query: str | None = None) -> list[Email]:
        if not 1 <= limit <= 500:
            raise ValueError("Email list limit must be between 1 and 500.")
        try:
            refs = []
            page_token = None
            while len(refs) < limit:
                args = {"userId": "me", "maxResults": min(100, limit - len(refs)), "pageToken": page_token}
                if query:
                    args["q"] = query
                result = self._gmail.users().messages().list(**args).execute()
                refs.extend(result.get("messages", []))
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
            messages = []
            for ref in refs[:limit]:
                email = self.get_email(ref.get("id", ""))
                if email is not None:
                    messages.append(email)
            return messages
        except GmailProviderError:
            raise
        except Exception as exc:
            raise GmailProviderError("Gmail message listing failed.") from exc

    def list_filtered_emails(self, filter_id: str, limit: int = 20) -> list[Email]:
        query = self.FILTER_QUERIES.get(filter_id)
        if query is None:
            raise ValueError("Unsupported email filter.")
        return self.list_emails(limit, query=query)

    def search_emails(self, query: str, limit: int = 10, *, sender_only: bool = False) -> list[Email]:
        clean_query = " ".join(str(query).split()).replace('"', "").replace("\\", "")
        if not clean_query or len(clean_query) > 200:
            raise ValueError("Email search query must contain between 1 and 200 characters.")
        if not 1 <= limit <= 500:
            raise ValueError("Email search limit must be between 1 and 500.")
        gmail_query = f'from:"{clean_query}"' if sender_only else f'"{clean_query}"'
        return self.list_emails(limit, query=gmail_query)
