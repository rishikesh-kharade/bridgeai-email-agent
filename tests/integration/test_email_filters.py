from tests.fakes import FakeEmailProvider
from app.schemas.email import Email


def email(email_id, *, is_read=False, labels=None, sender=None, subject=None, body="Message body"):
    return Email(
        id=email_id,
        provider_message_id=email_id,
        sender=sender or f"{email_id}@example.com",
        receiver="owner@example.com",
        subject=subject or email_id,
        body=body,
        is_read=is_read,
        labels=labels or [],
    )


def test_fake_email_adapter_returns_unread_candidates_for_semantic_filters():
    provider = FakeEmailProvider([
        email("important", labels=["IMPORTANT"]),
        email("read-important", is_read=True, labels=["IMPORTANT"]),
        email("escalated", labels=["Escalated"]),
        email("customer", labels=["Customer"]),
        email("ordinary"),
    ])

    assert [item.id for item in provider.list_filtered_emails("important_unread")] == ["important"]
    assert [item.id for item in provider.list_filtered_emails("unread")] == [
        "important", "escalated", "customer", "ordinary",
    ]


def test_local_email_search_matches_sender_or_message_content():
    provider = FakeEmailProvider([
        email("hopr", labels=[], sender="verification@hopr.mobi", subject="Verify your email", body="HOPR confirmation"),
        Email(id="other", provider_message_id="other", sender="newsletter@example.com",
              receiver="owner@example.com", subject="Planning", body="Project review"),
    ])
    assert [item.id for item in provider.search_emails("HOPR", sender_only=True)] == ["hopr"]
    assert [item.id for item in provider.search_emails("project review")] == ["other"]
