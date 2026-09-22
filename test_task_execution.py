import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.schemas.ai_analysis import AICategory, AIAnalysis
from app.services.task_execution_service import create_tasks_if_needed


def make_analysis(
    *,
    priority: str,
    requires_action: bool,
    requires_attention: bool,
    action_items: list[str] | None = None,
) -> AIAnalysis:
    return AIAnalysis(
        summary="The production system requires investigation.",
        category=AICategory(
            main="Technical Support",
            sub_category="Software Bug",
            group="Engineering",
        ),
        priority=priority,
        sentiment="Negative",
        requires_action=requires_action,
        requires_attention=requires_attention,
        action_items=action_items or [],
    )


class TaskExecutionDecisionTest(unittest.TestCase):
    @patch("app.services.task_execution_service.task_service.create_task")
    @patch(
        "app.services.task_execution_service.task_service.get_tasks_by_email_id"
    )
    def test_approved_analysis_create_task(
        self,
        get_tasks_by_email_id,
        create_task,
    ):
        get_tasks_by_email_id.return_value = []
        create_task.side_effect = [
            SimpleNamespace(id=101),
            SimpleNamespace(id=102),
        ]

        result = create_tasks_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Production Server Down",
            analysis=make_analysis(
                priority="High",
                requires_action=True,
                requires_attention=True,
                action_items=[
                    "Investigate the production outage",
                    "Inform the technical team",
                ],
            ),
        )

        self.assertTrue(result.task_created)
        self.assertEqual(create_task.call_count, 2)
        self.assertEqual(len(result.task_results), 2)
        self.assertEqual(result.task_results[0].task_id, 101)
        self.assertEqual(result.task_results[1].task_id, 102)

    @patch("app.services.task_execution_service.task_service.create_task")
    @patch(
        "app.services.task_execution_service.task_service.get_tasks_by_email_id"
    )
    def test_existing_task_prevents_duplicate(
        self,
        get_tasks_by_email_id,
        create_task,
    ):
        get_tasks_by_email_id.return_value = [
            SimpleNamespace(title="Investigate the production outage"),
        ]

        result = create_tasks_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Production Server Down",
            analysis=make_analysis(
                priority="High",
                requires_action=True,
                requires_attention=True,
                action_items=["Investigate the production outage!"],
            ),
        )

        self.assertFalse(result.task_created)
        self.assertFalse(result.task_results[0].task_created)
        create_task.assert_not_called()

    @patch("app.services.task_execution_service.task_service.create_task")
    @patch(
        "app.services.task_execution_service.task_service.get_tasks_by_email_id"
    )
    def test_unapproved_analysis_does_not_create_task(
        self,
        get_tasks_by_email_id,
        create_task,
    ):
        result = create_tasks_if_needed(
            db=object(),
            email_id=10,
            assigned_to_id=1,
            subject="Monthly Newsletter",
            analysis=make_analysis(
                priority="Low",
                requires_action=False,
                requires_attention=False,
            ),
        )

        self.assertFalse(result.task_created)
        self.assertEqual(result.task_results, [])
        get_tasks_by_email_id.assert_not_called()
        create_task.assert_not_called()


if __name__ == "__main__":
    unittest.main()