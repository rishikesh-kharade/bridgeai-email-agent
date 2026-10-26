from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.main import app
from app.api.routes.agent import build_router
from app.api.routes.emails import build_router as build_emails_router
from app.api.routes.meetings import build_router as build_meetings_router
from app.agents.graph import build_graph
from tests.fakes import FakeEmailProvider
from tests.fakes import FakeTaskProvider
from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.schemas.email import Email
from app.schemas.meeting import Meeting
from tests.fakes import FakeCalendarProvider
from app.schemas.email_triage import EmailTriageItem, EmailTriageResult
from app.services.ai_service import AgentToolCall, AgentTurn
from google.genai import types


class ScriptedModel:
    def __init__(self, turns):
        self.turns = iter(turns)

    def __call__(self, *_args, **_kwargs):
        return next(self.turns)


def tool(name, **arguments):
    return AgentTurn("", [AgentToolCall(name, arguments)], types.Content(role="model", parts=[]))


def answer(text):
    return AgentTurn(text, [], types.Content(role="model", parts=[]))


def test_local_ui_and_health_do_not_need_google_authorization():
    with TestClient(app) as client:
        page = client.get("/")
        health = client.get("/health")
        removed_user_route = client.get("/users")
    assert page.status_code == 200
    assert "BridgeAI Email Agent" in page.text
    assert 'id="root"' in page.text
    assert health.status_code == 200
    assert "x-request-id" not in health.headers
    assert removed_user_route.status_code == 404


def test_built_react_assets_are_served_by_the_local_app():
    with TestClient(app) as client:
        page = client.get("/")
        script_path = next(part.split('src="', 1)[1].split('"', 1)[0]
                           for part in page.text.split() if part.startswith("src=\"/assets/"))
        script = client.get(script_path)
    assert script.status_code == 200
    assert "Email Agent" in script.text
    assert "Runs on this computer" not in script.text


def test_meetings_route_returns_only_the_provider_contract():
    test_app = FastAPI()
    provider = FakeCalendarProvider([Meeting(
        id="meeting-1", title="Planning", start="2026-10-25T09:30:00+05:30",
    )])
    test_app.include_router(build_meetings_router(provider))
    with TestClient(test_app) as client:
        response = client.get("/meetings?limit=5")
    assert response.status_code == 200
    assert response.json()[0]["title"] == "Planning"


def test_open_email_route_returns_exact_full_message_and_404_for_missing_id():
    provider = FakeEmailProvider([Email(
        id="message-1", provider_message_id="message-1", sender="sender@example.com",
        receiver="owner@example.com", subject="Full message", body="Full body text.",
    )])
    test_app = FastAPI()
    test_app.include_router(build_emails_router(provider))
    with TestClient(test_app) as client:
        found = client.get("/emails/message-1")
        missing = client.get("/emails/unknown")
    assert found.status_code == 200
    assert found.json()["body"] == "Full body text."
    assert missing.status_code == 404


def test_chat_keeps_only_current_email_id_for_followup():
    emails = FakeEmailProvider([Email(
        id="1", provider_message_id="1", sender="sender@example.com",
        receiver="owner@example.com", subject="Project update", body="Please review.",
    )])
    analysis = AIAnalysis(
        summary="Review the update.", category=AICategory(main="Work"), priority="Medium",
        sentiment="Neutral", requires_action=True, requires_attention=True,
        action_items=["Review the update"],
    )
    graph = build_graph(emails, FakeTaskProvider(), model_turn=ScriptedModel([
        tool("list_recent_emails", limit=1), answer("Listed the latest email."),
        tool("review_email"), answer("Review the update."),
    ]), analyzer=lambda *_: analysis)
    test_app = FastAPI()
    test_app.include_router(build_router(graph))
    with TestClient(test_app) as client:
        listed = client.post("/agent/chat", json={"message": "Show the last email", "thread_id": "t1"})
        summarized = client.post("/agent/chat", json={"message": "Summarize this email", "thread_id": "t1"})
    assert listed.json()["current_email_id"] == "1"
    assert summarized.json()["response"] == "Review the update."


def test_filter_id_routes_through_the_agent_graph():
    emails = FakeEmailProvider([Email(
        id="important-1", provider_message_id="important-1", sender="sender@example.com",
        receiver="owner@example.com", subject="Review today", body="Please review.",
        is_read=False, labels=["IMPORTANT"],
    )])
    triage = EmailTriageResult(emails=[EmailTriageItem(
        index=1, summary="Review the request today.", priority="High",
        requires_action=True, requires_attention=True, action_items=["Review the request"],
    )])
    graph = build_graph(
        emails,
        FakeTaskProvider(),
        model_turn=ScriptedModel([answer("One important unread email needs review.")]),
        email_triage_classifier=lambda _excerpts: triage,
    )
    test_app = FastAPI()
    test_app.include_router(build_router(graph))
    with TestClient(test_app) as client:
        result = client.post("/agent/chat", json={
            "message": "Show unread important emails marked to me",
            "thread_id": "filter-test",
            "filter_id": "important_unread",
        })
    assert result.status_code == 200
    assert result.json()["email_options"][0]["subject"] == "Review today"
    assert result.json()["email_options"][0]["summary"] == "Review the request today."
    assert result.json()["email_options"][0]["priority"] == "High"
    assert result.json()["current_email_id"] == "important-1"


def test_chat_email_cards_select_exact_message_and_support_custom_task_title():
    emails = FakeEmailProvider([
        Email(id="first", provider_message_id="first", sender="one@example.com",
              receiver="owner@example.com", subject="First message", body="First body"),
        Email(id="second", provider_message_id="second", sender="two@example.com",
              receiver="owner@example.com", subject="FA_2 assessment", body="Review the FA_2 assessment."),
    ])
    tasks = FakeTaskProvider()
    analyzed = []
    analysis = AIAnalysis(
        summary="Review the assessment.", category=AICategory(main="Work"), priority="High",
        sentiment="Neutral", requires_action=True, requires_attention=True,
        action_items=["Review the assessment"],
    )
    graph = build_graph(emails, tasks, model_turn=ScriptedModel([
        tool("list_recent_emails", limit=2), answer("Here are both emails."),
        tool("create_task_from_email", task_title="FA_2 assessment follow-up"), answer("Task created."),
    ]), analyzer=lambda subject, body: (analyzed.append((subject, body)) or analysis))
    test_app = FastAPI()
    test_app.include_router(build_router(graph))

    with TestClient(test_app) as client:
        listed = client.post("/agent/chat", json={"message": "Show the last two emails", "thread_id": "cards"})
        created = client.post("/agent/chat", json={
            "message": "Analyze this email and create a task and name it FA_2 assessment follow-up",
            "thread_id": "cards",
            "selected_email_id": "second",
        })

    assert [item["subject"] for item in listed.json()["email_options"]] == ["First message", "FA_2 assessment"]
    assert analyzed == [("FA_2 assessment", "Review the FA_2 assessment.")]
    assert created.status_code == 200
    assert len(tasks.list_tasks()) == 1
    assert tasks.list_tasks()[0].source_email_id == "second"
    assert tasks.list_tasks()[0].title == "FA_2 assessment follow-up"


def test_agent_chat_rejects_unknown_filter_ids():
    with TestClient(app) as client:
        response = client.post("/agent/chat", json={
            "message": "Do something", "filter_id": "delete_all_emails",
        })
    assert response.status_code == 422
