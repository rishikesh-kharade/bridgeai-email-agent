from app.schemas.email import Email, EmailCreate, EmailUpdate


class InMemoryEmailProvider:
    """Development adapter only. Client production data does not live here."""

    def __init__(self, emails: list[Email] | None = None):
        self._emails = {email.id: email for email in (emails or [])}

    def get_email(self, email_id: str) -> Email | None:
        return self._emails.get(str(email_id))

    def list_emails(self, limit: int = 50) -> list[Email]:
        return list(self._emails.values())[:limit]

    def create_email(self, email: EmailCreate) -> Email:
        new_id = email.provider_message_id
        result = Email(id=new_id, **email.model_dump())
        self._emails[new_id] = result
        return result

    def update_email(self, email_id: str, email_update: EmailUpdate) -> Email | None:
        current = self.get_email(email_id)
        if current is None:
            return None
        updated = current.model_copy(update=email_update.model_dump(exclude_none=True))
        self._emails[str(email_id)] = updated
        return updated

    def mark_as_read(self, email_id: str) -> Email | None:
        return self.update_email(email_id, EmailUpdate(is_read=True))
