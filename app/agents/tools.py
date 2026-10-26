import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings
from app.core.logger import log_event
from app.schemas.ai_analysis import AIAnalysis
from app.services.task_execution_service import create_tasks_if_needed


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListEmailsArgs(_Args):
    limit: int = Field(default=10, ge=1, le=20)


class SearchEmailsArgs(_Args):
    query: str = Field(min_length=1, max_length=200)
    sender_only: bool = False
    limit: int = Field(default=10, ge=1, le=20)


class EmailIdArgs(_Args):
    email_id: str | None = Field(default=None, min_length=1, max_length=256)


class FilterArgs(_Args):
    filter_id: Literal["important_unread", "escalated_unread", "customer_unread"]
    limit: int = Field(default=20, ge=1, le=20)


class TaskArgs(EmailIdArgs):
    task_title: str | None = Field(default=None, max_length=300)


class MeetingArgs(_Args):
    limit: int = Field(default=20, ge=1, le=50)


@dataclass
class ToolOutcome:
    data: dict[str, Any]
    emails: list[Any] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    current_email_id: str | None = None
    clear_current_email: bool = False


TOOL_DECLARATIONS = [
    {"name": "list_recent_emails", "description": "List recent emails from the user's mailbox.", "parameters_json_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "additionalProperties": False}},
    {"name": "search_emails", "description": "Find matching emails. Set sender_only true only when looking for who sent an email; otherwise search subject and message content.", "parameters_json_schema": {"type": "object", "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 200}, "sender_only": {"type": "boolean"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": ["query"], "additionalProperties": False}},
    {"name": "get_email", "description": "Retrieve one exact email by ID, or the selected/current email when email_id is omitted.", "parameters_json_schema": {"type": "object", "properties": {"email_id": {"type": "string", "maxLength": 256}}, "additionalProperties": False}},
    {"name": "review_email", "description": "Analyze one exact email and return a validated summary, priority, action decision, and action items. Does not create a task.", "parameters_json_schema": {"type": "object", "properties": {"email_id": {"type": "string", "maxLength": 256}}, "additionalProperties": False}},
    {"name": "filter_unread_emails", "description": "Find unread important, escalated, or customer-related messages using semantic email review.", "parameters_json_schema": {"type": "object", "properties": {"filter_id": {"type": "string", "enum": ["important_unread", "escalated_unread", "customer_unread"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": ["filter_id"], "additionalProperties": False}},
    {"name": "list_tasks", "description": "List the user's tasks.", "parameters_json_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "list_meetings", "description": "List upcoming meetings from the configured calendar.", "parameters_json_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "additionalProperties": False}},
    {"name": "create_task_from_email", "description": "Create a follow-up task from an email only when the user explicitly asks. The application applies deterministic eligibility rules and duplicate prevention.", "parameters_json_schema": {"type": "object", "properties": {"email_id": {"type": "string", "maxLength": 256}, "task_title": {"type": "string", "maxLength": 300}}, "additionalProperties": False}},
]


class EmailAgentTools:
    def __init__(self, email_provider, task_provider, calendar_provider, *, analyzer, email_filter_classifier, email_triage_classifier):
        self.email_provider = email_provider
        self.task_provider = task_provider
        self.calendar_provider = calendar_provider
        self.analyzer = analyzer
        self.email_filter_classifier = email_filter_classifier
        self.email_triage_classifier = email_triage_classifier
        self._handlers: dict[str, tuple[type[_Args], Callable[..., ToolOutcome]]] = {
            "list_recent_emails": (ListEmailsArgs, self._list_emails),
            "search_emails": (SearchEmailsArgs, self._search_emails),
            "get_email": (EmailIdArgs, self._get_email),
            "review_email": (EmailIdArgs, self._review_email),
            "filter_unread_emails": (FilterArgs, self._filter_unread),
            "list_tasks": (_Args, self._list_tasks),
            "list_meetings": (MeetingArgs, self._list_meetings),
            "create_task_from_email": (TaskArgs, self._create_task),
        }

    def execute(self, name: str, arguments: dict[str, Any], state: dict[str, Any]) -> ToolOutcome:
        spec = self._handlers.get(name)
        if spec is None:
            return ToolOutcome({"error": "This operation is not available."})
        schema, handler = spec
        try:
            parsed = schema.model_validate(arguments or {})
            log_event("agent.tool.started", tool_name=name)
            outcome = handler(parsed, state)
            log_event("agent.tool.completed", tool_name=name, result_count=len(outcome.emails))
            return outcome
        except ValidationError:
            log_event("agent.tool.rejected", level=logging.WARNING, tool_name=name, reason="invalid_arguments")
            return ToolOutcome({"error": "The requested operation had invalid arguments. Please clarify the request."})
        except Exception as exc:
            log_event("agent.tool.failed", level=logging.ERROR, tool_name=name, error_type=type(exc).__name__)
            return ToolOutcome({"error": "The requested operation is temporarily unavailable. Please try again."})

    def _resolve_email_id(self, args: EmailIdArgs, state: dict[str, Any]) -> str | None:
        return args.email_id or state.get("selected_email_id") or state.get("current_email_id")

    def _list_emails(self, args: ListEmailsArgs, _state: dict[str, Any]) -> ToolOutcome:
        emails = self.email_provider.list_emails(min(args.limit, settings.max_email_list_limit))
        return ToolOutcome({"count": len(emails), "emails": [self._email_brief(email) for email in emails]}, emails=emails,
                           current_email_id=emails[0].id if emails else None, clear_current_email=not emails)

    def _search_emails(self, args: SearchEmailsArgs, _state: dict[str, Any]) -> ToolOutcome:
        emails = self.email_provider.search_emails(args.query, limit=args.limit, sender_only=args.sender_only)
        return ToolOutcome({"query": args.query, "count": len(emails), "emails": [self._email_brief(email) for email in emails]},
                           emails=emails, current_email_id=emails[0].id if emails else None,
                           clear_current_email=not emails)

    def _get_email(self, args: EmailIdArgs, state: dict[str, Any]) -> ToolOutcome:
        email_id = self._resolve_email_id(args, state)
        if not email_id:
            return ToolOutcome({"error": "Select an email or specify its exact email ID first."})
        email = self.email_provider.get_email(email_id)
        if email is None:
            return ToolOutcome({"error": "That exact email was not found or is inaccessible. No other email was substituted."},
                               clear_current_email=True)
        return ToolOutcome({"email": {**self._email_brief(email), "body": email.body[:settings.max_email_body_chars]}},
                           emails=[email], current_email_id=email.id)

    def _review_email(self, args: EmailIdArgs, state: dict[str, Any]) -> ToolOutcome:
        retrieved = self._get_email(args, state)
        if "email" not in retrieved.data:
            return retrieved
        email = retrieved.emails[0]
        analysis = self.analyzer(email.subject, email.body)
        review = self._analysis_dict(email.id, analysis)
        return ToolOutcome({"review": review}, emails=[email], reviews=[review], current_email_id=email.id)

    def _filter_unread(self, args: FilterArgs, _state: dict[str, Any]) -> ToolOutcome:
        unread = self.email_provider.list_filtered_emails("unread", limit=min(args.limit, settings.max_email_filter_scan))
        if not unread:
            return ToolOutcome({"filter": args.filter_id, "count": 0, "emails": []}, clear_current_email=True)
        excerpts = [{"sender": str(email.sender), "subject": email.subject, "body": email.body} for email in unread]
        if args.filter_id == "important_unread":
            triage = self.email_triage_classifier(excerpts)
            by_index = {item.index: item for item in triage.emails}
            matched = [(email, by_index[index]) for index, email in enumerate(unread, start=1)
                       if index in by_index and by_index[index].priority in {"Critical", "High"}]
            emails = [email for email, _item in matched]
            reviews = [self._triage_dict(email.id, item) for email, item in matched]
        else:
            classification = self.email_filter_classifier(excerpts, args.filter_id)
            indices = set(classification.matching_indices)
            emails = [email for index, email in enumerate(unread, start=1) if index in indices]
            reviews = []
        return ToolOutcome({"filter": args.filter_id, "reviewed_count": len(unread), "count": len(emails),
                            "emails": [self._email_brief(email) for email in emails], "reviews": reviews},
                           emails=emails, reviews=reviews, current_email_id=emails[0].id if emails else None,
                           clear_current_email=not emails)

    def _list_tasks(self, _args: _Args, _state: dict[str, Any]) -> ToolOutcome:
        tasks = self.task_provider.list_tasks()[:50]
        return ToolOutcome({"count": len(tasks), "tasks": [{"title": task.title, "status": task.status,
                                                               "priority": task.priority} for task in tasks]})

    def _list_meetings(self, args: MeetingArgs, _state: dict[str, Any]) -> ToolOutcome:
        if self.calendar_provider is None:
            return ToolOutcome({"error": "Calendar access is not configured."})
        meetings = self.calendar_provider.list_upcoming_meetings(args.limit)
        return ToolOutcome({"count": len(meetings), "meetings": [meeting.model_dump(mode="json") for meeting in meetings]})

    def _create_task(self, args: TaskArgs, state: dict[str, Any]) -> ToolOutcome:
        email_id = self._resolve_email_id(args, state)
        if not email_id:
            return ToolOutcome({"error": "Select an email or specify its exact email ID before creating a task."})
        email = self.email_provider.get_email(email_id)
        if email is None:
            return ToolOutcome({"error": "That exact email was not found or is inaccessible. No task was created."},
                               clear_current_email=True)
        analysis = self.analyzer(email.subject, email.body)
        result = create_tasks_if_needed(self.task_provider, email_id=email.id, subject=email.subject,
                                        analysis=analysis, task_title=args.task_title)
        return ToolOutcome({"task_created": result.task_created, "message": result.message,
                            "decision": result.decision.reason}, emails=[email], current_email_id=email.id)

    @staticmethod
    def _email_brief(email: Any) -> dict[str, Any]:
        return {"id": email.id, "sender": str(email.sender), "subject": email.subject,
                "received_at": email.received_at.isoformat() if email.received_at else None,
                "is_read": email.is_read}

    @staticmethod
    def _analysis_dict(email_id: str, result: AIAnalysis) -> dict[str, Any]:
        return {"email_id": email_id, "summary": result.summary, "priority": result.priority,
                "requires_action": result.requires_action, "requires_attention": result.requires_attention,
                "action_items": result.action_items}

    @staticmethod
    def _triage_dict(email_id: str, item: Any) -> dict[str, Any]:
        return {"email_id": email_id, "summary": item.summary, "priority": item.priority,
                "requires_action": item.requires_action, "requires_attention": item.requires_attention,
                "action_items": item.action_items}
