from google.genai import types

from app.agents.graph import build_graph
from tests.fakes import FakeEmailProvider
from tests.fakes import FakeTaskProvider
from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.schemas.email import Email
from app.schemas.email_filter import EmailFilterClassification
from app.schemas.email_triage import EmailTriageItem, EmailTriageResult
from app.services.ai_service import AgentToolCall, AgentTurn


def make_analysis(priority="High", requires_action=True):
    return AIAnalysis(summary="Please review this.", category=AICategory(main="Work"),
                      priority=priority, sentiment="Neutral", requires_action=requires_action,
                      requires_attention=True, action_items=["Review the request"] if requires_action else [])


def make_email(email_id="one", subject="Project update", body="Please review this update.", sender="sender@example.com", is_read=False):
    return Email(id=email_id, provider_message_id=email_id, sender=sender, receiver="owner@example.com",
                 subject=subject, body=body, is_read=is_read)


class ScriptedModel:
    def __init__(self, turns):
        self.turns = iter(turns)
        self.calls = []

    def __call__(self, messages, declarations, system_instruction, *, tools_enabled=True):
        self.calls.append((messages, declarations, system_instruction, tools_enabled))
        return next(self.turns)


def call_tool(name, **arguments):
    return AgentTurn("", [AgentToolCall(name, arguments)], types.Content(role="model", parts=[]))


def answer(text):
    return AgentTurn(text, [], types.Content(role="model", parts=[]))


def test_free_form_request_is_sent_to_gemini_and_tool_result_returns_for_answer():
    email = make_email()
    provider = FakeEmailProvider([email])
    model = ScriptedModel([call_tool("list_recent_emails", limit=5), answer("Here is your latest email: Project update.")])
    graph = build_graph(provider, FakeTaskProvider(), model_turn=model)

    result = graph.invoke({"message": "Could you show me the newest messages when you have a moment?"})

    assert len(model.calls) == 2
    assert "Could you show me the newest messages" in model.calls[0][0][0].parts[0].text
    assert any(item["name"] == "search_emails" for item in model.calls[0][1])
    assert result["response"] == "Here is your latest email: Project update."
    assert [item.id for item in result["email_results"]] == ["one"]


def test_search_sender_uses_only_matching_email_and_never_recent_fallback():
    provider = FakeEmailProvider([
        make_email("unrelated", "Newsletter", "General update", "other@example.com"),
        make_email("match", "Verify account", "Verification", "karthik@example.com"),
    ])
    model = ScriptedModel([call_tool("search_emails", query="Karthik", sender_only=True), answer("Found one email sent by Karthik.")])
    graph = build_graph(provider, FakeTaskProvider(), model_turn=model)

    result = graph.invoke({"message": "Can you check if Karthik sent me anything?"})

    assert [email.id for email in result["email_results"]] == ["match"]
    assert result["current_email_id"] == "match"


def test_exact_email_missing_does_not_substitute_another_email():
    graph = build_graph(FakeEmailProvider([make_email("existing")]), FakeTaskProvider(),
                        model_turn=ScriptedModel([call_tool("get_email", email_id="missing"), answer("No exact match.")]))

    result = graph.invoke({"message": "Open the message", "selected_email_id": "missing"})

    assert result["email_results"] == []
    assert result.get("current_email_id") is None
    assert "No exact match" in result["response"]


def test_important_unread_preset_returns_high_critical_summaries_without_task_creation():
    provider = FakeEmailProvider([
        make_email("high", "Urgent request", "Please respond today."),
        make_email("low", "Newsletter", "Read when free."),
    ])
    triage = EmailTriageResult(emails=[
        EmailTriageItem(index=1, summary="Reply today.", priority="High", requires_action=True,
                        requires_attention=True, action_items=["Reply"]),
        EmailTriageItem(index=2, summary="Newsletter.", priority="Low", requires_action=False,
                        requires_attention=False),
    ])
    model = ScriptedModel([answer("One unread important email needs attention.")])
    tasks = FakeTaskProvider()
    graph = build_graph(provider, tasks, model_turn=model, email_triage_classifier=lambda _items: triage)

    result = graph.invoke({"message": "Unread important", "filter_id": "important_unread"})

    assert [email.id for email in result["email_results"]] == ["high"]
    assert result["email_reviews"][0]["summary"] == "Reply today."
    assert tasks.list_tasks() == []


def test_task_is_created_only_after_tool_call_and_deterministic_approval():
    provider, tasks = FakeEmailProvider([make_email()]), FakeTaskProvider()
    model = ScriptedModel([call_tool("create_task_from_email", email_id="one", task_title="Review update"),
                           answer("Created the eligible task.")])
    graph = build_graph(provider, tasks, model_turn=model, analyzer=lambda *_: make_analysis())

    result = graph.invoke({"message": "Please create a follow-up task for this email.", "selected_email_id": "one"})

    assert result["response"] == "Created the eligible task."
    assert len(tasks.list_tasks()) == 1
    assert tasks.list_tasks()[0].title == "Review update"


def test_rejected_task_rule_creates_nothing():
    provider, tasks = FakeEmailProvider([make_email()]), FakeTaskProvider()
    model = ScriptedModel([call_tool("create_task_from_email", email_id="one"), answer("No task was created.")])
    graph = build_graph(provider, tasks, model_turn=model, analyzer=lambda *_: make_analysis("Low"))

    graph.invoke({"message": "Make a task from this", "selected_email_id": "one"})

    assert tasks.list_tasks() == []


def test_tool_loop_is_bounded():
    model = ScriptedModel([call_tool("list_recent_emails") for _ in range(2)])
    graph = build_graph(FakeEmailProvider([make_email()]), FakeTaskProvider(), model_turn=model, max_tool_calls=1)

    result = graph.invoke({"message": "Keep doing more"})

    assert len(model.calls) == 2
    assert model.calls[-1][3] is False
    assert "safe limit" in result["response"]


def test_tool_arguments_are_validated_before_provider_access():
    class NeverCalledProvider(FakeEmailProvider):
        def list_emails(self, limit=50):
            raise AssertionError("invalid limits must be rejected before provider access")

    model = ScriptedModel([call_tool("list_recent_emails", limit=500), answer("The limit was rejected.")])
    graph = build_graph(NeverCalledProvider(), FakeTaskProvider(), model_turn=model)

    result = graph.invoke({"message": "List many emails"})

    assert "invalid arguments" in model.calls[1][0][-1].parts[0].function_response.response["error"]
    assert "rejected" in result["response"]


def test_semantic_email_filter_does_not_require_provider_label():
    provider = FakeEmailProvider([make_email("e1", "Unresolved outage", "Request management intervention.")])
    graph = build_graph(provider, FakeTaskProvider(),
                        model_turn=ScriptedModel([answer("Found an escalated issue.")]),
                        email_filter_classifier=lambda _items, _filter: EmailFilterClassification(matching_indices=[1]))

    result = graph.invoke({"message": "Show escalated issues", "filter_id": "escalated_unread"})

    assert [email.id for email in result["email_results"]] == ["e1"]
