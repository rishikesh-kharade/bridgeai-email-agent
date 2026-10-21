from app.integrations.email.local_provider import InMemoryEmailProvider
from app.integrations.tasks.local_provider import InMemoryTaskProvider
from app.schemas.email import Email


def test_email_provider():
    provider = InMemoryEmailProvider([Email(
        id="1", provider_message_id="1", sender="a@example.com",
        receiver="b@example.com", subject="Hello", body="Body"
    )])
    assert provider.get_email("1").subject == "Hello"
    assert len(provider.list_emails()) == 1


def test_task_provider():
    provider = InMemoryTaskProvider()
    assert provider.get_task_count() == 0
