from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.main import app
from app.api.routes.agent import build_router
from app.agents.graph import build_graph
from app.integrations.email.local_provider import InMemoryEmailProvider
from app.integrations.tasks.local_provider import InMemoryTaskProvider
from app.schemas.ai_analysis import AIAnalysis, AICategory
from app.schemas.email import Email


def test_local_ui_and_health_do_not_need_google_authorization():
    with TestClient(app) as client:
        page = client.get("/")
        health = client.get("/health")
        removed_user_route = client.get("/users")
    assert page.status_code == 200
    assert "BridgeAI Email Assistant" in page.text
    assert health.status_code == 200
    assert removed_user_route.status_code == 404


def test_chat_keeps_only_current_email_id_for_followup():
    emails = InMemoryEmailProvider([Email(
        id="1", provider_message_id="1", sender="sender@example.com",
        receiver="owner@example.com", subject="Project update", body="Please review.",
    )])
    analysis = AIAnalysis(
        summary="Review the update.", category=AICategory(main="Work"), priority="Medium",
        sentiment="Neutral", requires_action=True, requires_attention=True,
        action_items=["Review the update"],
    )
    graph = build_graph(emails, InMemoryTaskProvider(), analyzer=lambda *_: analysis)
    test_app = FastAPI()
    test_app.include_router(build_router(graph))
    with TestClient(test_app) as client:
        listed = client.post("/agent/chat", json={"message": "Show the last email", "thread_id": "t1"})
        summarized = client.post("/agent/chat", json={"message": "Summarize this email", "thread_id": "t1"})
    assert listed.json()["current_email_id"] == "1"
    assert summarized.json()["response"] == "Review the update."
