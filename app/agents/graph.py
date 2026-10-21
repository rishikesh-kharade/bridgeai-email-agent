"""Small, conditional email workflow; all provider/model calls are injectable."""
import re
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.core.logger import logger
from app.schemas.ai_analysis import AIAnalysis
from app.agents.state import EmailAgentState
from app.services.ai_service import AIServiceConfigurationError, analyze_email, answer_email_question
from app.services.task_execution_service import create_tasks_if_needed


_ID_PATTERN = re.compile(r"\b(?:email|message)\s+(?:id\s+|#)?([A-Za-z0-9_-]+)\b", re.I)
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _intent(text: str, current_email_id: str | None = None) -> tuple[str, bool, str | None, int]:
    lowered = text.lower()
    wants_task = any(term in lowered for term in ("create a task", "make a task", "create task", "add a task"))
    if any(term in lowered for term in ("analyze", "analyse", "action item", "requires action", "what should i do", "do i need to reply", "reply needed")):
        intent = "analyze"
    elif any(term in lowered for term in ("summarize", "summary", "brief me", "what is this about", "what's this about", "explain this email")):
        intent = "summary"
    elif any(term in lowered for term in ("show my tasks", "list my tasks", "what are my tasks", "my tasks", "show tasks", "list tasks", "my task list")):
        return "tasks", False, None, 10
    else:
        intent = ""
    if intent in {"summary", "analyze"}:
        # Only treat a token as an email ID when the user labels it as one.
        # Otherwise ordinary long words in a custom task title (for example,
        # "Modelling") can be mistaken for IDs and sent to Gmail.
        ids = _ID_PATTERN.findall(text)
        email_id = ids[-1] if ids else None
        if not email_id and any(term in lowered for term in ("this email", "that email", "this mail", "that mail", "summarize it", "summarize that", "summarize this", "analyze it", "analyze that", "analyse it", "that one", "last one")):
            email_id = current_email_id
        return intent, wants_task, email_id, 10
    if any(term in lowered for term in ("list emails", "show emails", "recent emails", "last ", "inbox")):
        match = re.search(r"\b(?:last|show|list)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", lowered)
        count = int(match.group(1)) if match and match.group(1).isdigit() else _NUMBER_WORDS.get(match.group(1), 10) if match else 10
        return "list", wants_task, None, min(max(count, 1), settings.max_email_list_limit)
    ids = _ID_PATTERN.findall(text)
    # Accept a conservative exact token; never substitute another provider result.
    email_id = ids[-1] if ids else None
    if wants_task and not email_id:
        # A task request must not guess which of several recently listed emails
        # "it" means. The caller can pick an email or supply its exact ID.
        return "unknown", wants_task, None, 10
    referential = any(term in lowered for term in ("this email", "that email", "this mail", "that mail", "this one", "that one", "it"))
    if email_id and any(term in lowered for term in ("get email", "retrieve email", "open email", "show email")):
        return "retrieve", wants_task, email_id, 10
    if email_id or (referential and current_email_id):
        return "question", wants_task, email_id or current_email_id, 10
    if email_id:
        return "retrieve", wants_task, email_id, 10
    return "unknown", wants_task, None, 10


def build_graph(email_provider, task_provider, *, analyzer=analyze_email, question_answerer=answer_email_question):
    """Build a dependency-injected graph suitable for tests and local execution."""

    def understand(state: EmailAgentState):
        intent, wants_task, email_id, email_limit = _intent(
            state.get("message", ""), state.get("current_email_id")
        )
        return {"intent": intent, "requested_task": wants_task, "email_id": email_id, "email_limit": email_limit}

    def list_node(state: EmailAgentState):
        emails = email_provider.list_emails(state.get("email_limit", 10))
        if not emails:
            response = "No emails were found."
        else:
            rows = []
            for index, email in enumerate(emails, start=1):
                received = f" · {email.received_at.isoformat()}" if email.received_at else ""
                rows.append(f"{index}. {email.subject} — from {email.sender}{received}")
            response = "Recent emails:\n" + "\n".join(rows)
        return {"response": response, "current_email_id": emails[0].id if emails else state.get("current_email_id")}

    def tasks_node(_state: EmailAgentState):
        tasks = task_provider.list_tasks()
        if not tasks:
            return {"response": "You have no tasks in your BridgeAI task list."}
        return {"response": "\n".join(f"{task.title} · {task.status}" for task in tasks[:50])}

    def retrieve_node(state: EmailAgentState):
        email_id = state.get("email_id")
        if not email_id:
            return {"response": "Please include the exact email ID you want me to retrieve or analyze."}
        email = email_provider.get_email(email_id)
        if email is None:
            return {"response": f"Email {email_id} was not found.", "current_email_id": None}
        return {"email": email, "current_email_id": email.id}

    def summarize_node(state: EmailAgentState):
        email = state["email"]
        try:
            result = analyzer(email.subject, email.body)
        except AIServiceConfigurationError:
            return {"response": "Email analysis is not configured. Set GEMINI_API_KEY and try again."}
        except Exception as exc:
            # Keep diagnostics useful without logging the email, prompt, or API key.
            logger.warning(
                "Gemini email analysis failed (error_type=%s, status_code=%s, api_status=%s)",
                type(exc).__name__, getattr(exc, "code", None), getattr(exc, "status", None),
            )
            return {"response": "Email analysis is temporarily unavailable. Please try again."}
        if state.get("intent") == "summary" and not state.get("requested_task"):
            return {"response": result.summary}
        return {"analysis": result}

    def question_node(state: EmailAgentState):
        email = state["email"]
        try:
            response = question_answerer(state.get("message", ""), email.subject, email.body)
        except AIServiceConfigurationError:
            response = "Email questions need Gemini. Set GEMINI_API_KEY and try again."
        except Exception as exc:
            logger.warning(
                "Gemini email question failed (error_type=%s, status_code=%s, api_status=%s)",
                type(exc).__name__, getattr(exc, "code", None), getattr(exc, "status", None),
            )
            response = "Email question answering is temporarily unavailable. Please try again."
        return {"response": response}

    def task_node(state: EmailAgentState):
        email = state["email"]
        analysis = state["analysis"]
        if not state.get("requested_task"):
            return {"response": _analysis_text(analysis)}
        try:
            result = create_tasks_if_needed(
                task_provider,
                email_id=email.id,
                subject=email.subject,
                analysis=analysis,
            )
        except Exception:
            return {"response": _analysis_text(analysis) + "\nTask provider is unavailable; no task result was confirmed."}
        return {"response": _analysis_text(analysis) + "\n" + result.message}

    def route_intent(state: EmailAgentState):
        if state["intent"] == "list":
            return "list"
        if state["intent"] == "tasks":
            return "tasks"
        if state["intent"] == "unknown":
            return "unknown"
        return "retrieve"

    def route_after_retrieve(state: EmailAgentState):
        if "email" not in state:
            return "finish"
        if state["intent"] in {"summary", "analyze"} or state.get("requested_task"):
            return "summarize"
        if state["intent"] == "question":
            return "question"
        return "retrieve_only"

    def simple_retrieve_response(state: EmailAgentState):
        email = state["email"]
        return {"response": f"Email {email.id}: {email.subject}\nFrom: {email.sender}"}

    def unknown_node(state: EmailAgentState):
        if state.get("requested_task"):
            return {"response": (
                "I can create an eligible follow-up task from an email. Select that email's "
                "Analyze & create eligible tasks button or provide its exact email ID. "
                "Standalone tasks with a custom title are not supported yet."
            )}
        return {"response": "I can list recent emails, retrieve an email by ID, summarize it, or analyze action items."}

    def route_after_analysis(state: EmailAgentState):
        if "analysis" in state:
            return "task"
        return "finish"

    graph = StateGraph(EmailAgentState)
    for name, node in (
        ("understand", understand), ("list", list_node), ("retrieve", retrieve_node),
        ("summarize", summarize_node), ("task", task_node),
        ("question", question_node), ("simple_retrieve", simple_retrieve_response), ("tasks", tasks_node), ("unknown", unknown_node),
    ):
        graph.add_node(name, node)
    graph.add_edge(START, "understand")
    graph.add_conditional_edges("understand", route_intent, {
        "list": "list", "retrieve": "retrieve", "tasks": "tasks", "unknown": "unknown",
    })
    graph.add_edge("list", END)
    graph.add_edge("tasks", END)
    graph.add_edge("unknown", END)
    graph.add_conditional_edges("retrieve", route_after_retrieve, {
        "summarize": "summarize", "finish": END,
        "retrieve_only": "simple_retrieve",
        "question": "question",
    })
    graph.add_conditional_edges("summarize", route_after_analysis, {
        "task": "task", "finish": END,
    })
    graph.add_edge("task", END)
    graph.add_edge("simple_retrieve", END)
    graph.add_edge("question", END)
    return graph.compile()


def _analysis_text(analysis: AIAnalysis) -> str:
    actions = "\n".join(f"- {item}" for item in analysis.action_items) or "- None"
    return (
        f"Summary: {analysis.summary}\nPriority: {analysis.priority}\n"
        f"Requires action: {analysis.requires_action}\nAction items:\n{actions}"
    )
