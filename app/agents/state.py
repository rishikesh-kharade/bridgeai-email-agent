from typing import Any, TypedDict


class EmailAgentState(TypedDict, total=False):
    message: str
    filter_id: str | None
    selected_email_id: str | None
    current_email_id: str | None
    messages: list[Any]
    tool_calls: list[Any]
    tool_call_count: int
    response: str
    email_results: list[Any]
    email_reviews: list[dict[str, Any]]
    clear_current_email: bool


__all__ = ["EmailAgentState"]
