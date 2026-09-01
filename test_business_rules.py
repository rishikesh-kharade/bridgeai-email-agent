import unittest

from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.services.task_decision_service import decide_task_creation


def make_analysis(
        *,
        priority: str,
        requires_action: bool,
        requires_attention: bool,
) -> AIAnalysis:
    return AIAnalysis(
        summary="Test email analysis",
        category=AICategory(main="Any dynamic category"),
        priority=priority,
        sentiment="Neutral",
        requires_action=requires_action,
        requires_attention=requires_attention,
        action_items=[],
    )

class TaskDecisionServiceTest(unittest.TestCase):
    def test_critical_action_creates_task(self):
        decision = decide_task_creation(
            make_analysis(
                priority="Critical",
                requires_action=True,
                requires_attention=True,
            )
        )

        self.assertTrue(decision.should_create_task)
        self.assertEqual(decision.recommended_priority, "Critical")

    def test_medium_attention_action_creates_task(self):
        decision = decide_task_creation(
            make_analysis(
                priority="Medium",
                requires_action=True,
                requires_attention=True,
            )
        )

        self.assertTrue(decision.should_create_task)

    def test_low_priority_action_does_not_create_task(self):
        decision = decide_task_creation(
            make_analysis(
                priority="Low",
                requires_action=True,
                requires_attention=False,
            )
        )

        self.assertFalse(decision.should_create_task)

    def test_no_action_never_creates_task(self):
        decision = decide_task_creation(
            make_analysis(
                priority="Critical",
                requires_action=False,
                requires_attention=True,
            )
        )

        self.assertFalse(decision.should_create_task)

if __name__ == '__main__':
    unittest.main()