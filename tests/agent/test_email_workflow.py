from app.agents.graph import build_graph
from app.integrations.email.local_provider import InMemoryEmailProvider
from app.integrations.tasks.local_provider import InMemoryTaskProvider
from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.schemas.email import Email


def make_analysis(priority="High", requires_action=True):
    return AIAnalysis(
        summary="Please review the contract.",
        category=AICategory(main="Legal"),
        priority=priority,
        sentiment="Neutral",
        requires_action=requires_action,
        requires_attention=True,
        action_items=["Review the contract"] if requires_action else [],
    )


def providers():
    email = Email(
        id="1", provider_message_id="1", sender="sender@example.com",
        receiver="receiver@example.com", subject="Contract review", body="Please review.",
    )
    emails = InMemoryEmailProvider([email])
    tasks = InMemoryTaskProvider()
    return emails, tasks


def test_list_flow_does_not_call_model():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: (_ for _ in ()).throw(AssertionError("unexpected model call")))
    result = graph.invoke({"message": "Show last five emails"})
    assert "Contract review" in result["response"]
    assert "sender@example.com" in result["response"]
    assert "1 | sender@example.com" not in result["response"]


def test_list_flow_respects_requested_count():
    class CountingProvider(InMemoryEmailProvider):
        received_limit = None

        def list_emails(self, limit=50):
            self.received_limit = limit
            return super().list_emails(limit)

    email = Email(id="1", provider_message_id="1", sender="a@example.com",
                  receiver="b@example.com", subject="Hello", body="Body")
    provider = CountingProvider([email])
    graph = build_graph(provider, InMemoryTaskProvider(), analyzer=lambda *_: None)
    graph.invoke({"message": "Show the last five emails"})
    assert provider.received_limit == 5


def test_tasks_can_be_listed_in_chat():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: None)
    assert "no tasks" in graph.invoke({"message": "Show my tasks"})["response"].lower()


def test_summary_retrieves_exact_email_and_does_not_create_task():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: make_analysis())
    result = graph.invoke({"message": "Summarize email 1"})
    assert result["response"] == "Please review the contract."
    assert result["current_email_id"] == "1"
    assert tasks.list_tasks() == []


def test_summary_can_refer_to_current_email_by_context():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: make_analysis())
    result = graph.invoke({"message": "Summarize this email", "current_email_id": "1"})
    assert result["response"] == "Please review the contract."
    assert result["current_email_id"] == "1"


def test_chat_can_answer_a_question_about_an_exact_email():
    emails, tasks = providers()
    graph = build_graph(
        emails, tasks,
        question_answerer=lambda question, subject, body: f"Answer based on {subject}: {question}",
    )
    result = graph.invoke({"message": "Who sent email 1?"})
    assert "Contract review" in result["response"]
    assert "Who sent email 1?" in result["response"]


def test_exact_missing_id_never_substitutes_another_email():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: make_analysis())
    result = graph.invoke({"message": "Summarize email 2"})
    assert "Email 2 was not found" in result["response"]
    assert result.get("current_email_id") is None


def test_task_creation_requires_explicit_request_and_decision():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: make_analysis())
    no_task = graph.invoke({"message": "Analyze email 1"})
    assert tasks.list_tasks() == []
    assert "Summary:" in no_task["response"]

    requested = graph.invoke({
        "message": "Analyze email 1 and create a task if action is required",
    })
    assert len(tasks.list_tasks()) == 1
    assert "1 task(s) created" in requested["response"]


def test_task_rule_rejection_is_respected():
    emails, tasks = providers()
    graph = build_graph(emails, tasks, analyzer=lambda *_: make_analysis("Low"))
    graph.invoke({
        "message": "Analyze email 1 and create a task",
    })
    assert tasks.list_tasks() == []


def test_custom_task_title_is_not_mistaken_for_email_id():
    class NoEmailLookup(InMemoryEmailProvider):
        def get_email(self, email_id):
            raise AssertionError(f"unexpected Gmail lookup for {email_id!r}")

    emails, tasks = providers()
    emails = NoEmailLookup([emails.get_email("1")])
    graph = build_graph(emails, tasks)
    result = graph.invoke({
        "message": "Perfect now create a Task for it and name it FA_2 Product Data Modelling course",
        "current_email_id": "1",
    })
    assert "Standalone tasks with a custom title are not supported yet" in result["response"]
    assert tasks.list_tasks() == []
