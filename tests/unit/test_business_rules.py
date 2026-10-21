from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.services.task_decision_service import decide_task_creation


def analysis(priority, action=True, attention=True):
    return AIAnalysis(
        summary="summary",
        category=AICategory(main="Operations"),
        priority=priority,
        sentiment="Neutral",
        requires_action=action,
        requires_attention=attention,
        action_items=["Investigate issue"] if action else [],
    )


def test_critical_creates_task():
    assert decide_task_creation(analysis("Critical")).should_create_task is True


def test_high_creates_task():
    assert decide_task_creation(analysis("High")).should_create_task is True


def test_medium_requires_attention():
    assert decide_task_creation(analysis("Medium", attention=False)).should_create_task is False
    assert decide_task_creation(analysis("Medium", attention=True)).should_create_task is True


def test_low_does_not_create_task():
    assert decide_task_creation(analysis("Low")).should_create_task is False


def test_no_action_never_creates_task():
    assert decide_task_creation(analysis("Critical", action=False)).should_create_task is False
