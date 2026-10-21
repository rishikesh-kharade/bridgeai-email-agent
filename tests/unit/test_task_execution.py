from app.integrations.tasks.local_provider import InMemoryTaskProvider
from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.services.task_execution_service import create_tasks_if_needed


def test_task_execution_is_idempotent_for_same_email_and_action():
    provider = InMemoryTaskProvider()
    analysis = AIAnalysis(
        summary="Review the request.",
        category=AICategory(main="Operations"),
        priority="high",
        sentiment="Neutral",
        requires_action=True,
        requires_attention=True,
        action_items=["Review the request"],
    )
    args = dict(email_id="mail-1", subject="Request", analysis=analysis)
    first = create_tasks_if_needed(provider, **args)
    second = create_tasks_if_needed(provider, **args)
    assert first.task_created is True
    assert second.task_created is False
    assert len(provider.list_tasks()) == 1


def test_no_action_items_fails_closed():
    analysis = AIAnalysis(
        summary="Unclear request.",
        category=AICategory(main="Other"),
        priority="Critical",
        sentiment="Neutral",
        requires_action=True,
        requires_attention=True,
        action_items=[],
    )
    result = create_tasks_if_needed(
        InMemoryTaskProvider(), email_id="mail-2",
        subject="Unclear", analysis=analysis,
    )
    assert result.task_created is False
    assert "no validated action items" in result.decision.reason
