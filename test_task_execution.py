import unittest

from types import SimpleNamespace
from unittest.mock import patch

from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.services.task_execution_service import create_task_if_needed


def make_analysis(
        *,
        priority: str,
        requires_action: bool,
        requires_attention: bool,
        action_items: list[str] | None = None,
) -> AIAnalysis:
    return AIAnalysis(
        summary="The production service needs investigation.",
        category=AICategory(
            main="IT Infrastructure",
            sub_category="Server Outage",
        ),
        priority=priority,
        sentiment="Negative",
        requires_action=requires_action,
        requires_attention=requires_attention,
        action_items=action_items or [],
    )

class TaskExecutionDecisionTest(unittest.TestCase):

    @patch('app.services.task_execution_service.task_service.create_task')

    @patch('app.services.task_execution_service.task_service.get_task_by_email_id')

    def test_approved_analysis_create_task(self, get_task_by_email_id, create_task):
        get_task_by_email_id.return_value = None
        create_task.return_value = SimpleNamespace(id=101)

        result = create_task_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Production Server Down",
            description="Customers cannot access the production application",
            analysis=make_analysis(
                priority="Critical",
                requires_action=True,
                requires_attention=True,
                action_items=["Investigate the production outage"],
            ),
        )

        self.assertTrue(result.decision.should_create_task)
        self.assertTrue(result.task_created)
        self.assertEqual(result.task_id, 101)

        create_task.assert_called_once()

    @patch('app.services.task_execution_service.task_service.create_task')
    @patch('app.services.task_execution_service.task_service.get_task_by_email_id')

    def test_unapproved_analysis_does_not_create_task(
        self,
        get_task_by_email_id,
        create_task,
    ):

        result = create_task_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Monthly Newsletter",
            description="Customers cannot access the production application",
            analysis=make_analysis(
                priority="Low",
                requires_action=False,
                requires_attention=False,
            ),
        )

        self.assertFalse(result.decision.should_create_task)
        self.assertFalse(result.task_created)
        get_task_by_email_id.assert_not_called()
        create_task.assert_not_called()

    @patch("app.services.task_execution_service.task_service.create_task")
    @patch('app.services.task_execution_service.task_service.get_task_by_email_id')

    def test_existing_task_prevents_duplicate(
            self,
            get_task_by_email_id,
            create_task,
    ):
        get_task_by_email_id.return_value = SimpleNamespace(id=55)

        result = create_task_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Production Server Down",
            description="Customers cannot access the production application",
            analysis=make_analysis(
                priority="High",
                requires_action=True,
                requires_attention=True,
            ),
        )

        self.assertTrue(result.decision.should_create_task)
        self.assertFalse(result.task_created)
        self.assertEqual(result.task_id, 55)
        create_task.assert_not_called()


if __name__ == "__main__":
    unittest.main()

