import logging
from functools import wraps
from time import perf_counter

from google.genai import types
from langgraph.graph import END, START, StateGraph

from app.agents.state import EmailAgentState
from app.agents.tools import EmailAgentTools, TOOL_DECLARATIONS
from app.core.logger import log_event, logger
from app.prompts.agent_system_prompt import build_agent_system_prompt
from app.services.ai_service import AIServiceConfigurationError, agent_turn
from app.services.ai_service import analyze_email, classify_email_filter, triage_emails


MAX_TOOL_CALLS = 5
PRESET_TOOL_CALLS = {
    "important_unread": ("filter_unread_emails", {"filter_id": "important_unread"}),
    "escalated_unread": ("filter_unread_emails", {"filter_id": "escalated_unread"}),
    "customer_unread": ("filter_unread_emails", {"filter_id": "customer_unread"}),
    "my_tasks": ("list_tasks", {}),
    "my_meetings": ("list_meetings", {}),
}


def _observe_node(name, node):
    @wraps(node)
    def observed(state: EmailAgentState):
        started = perf_counter()
        log_event("workflow.step.started", workflow_step=name)
        try:
            result = node(state)
        except Exception as exc:
            log_event("workflow.step.failed", level=logging.ERROR, workflow_step=name,
                      duration_ms=round((perf_counter() - started) * 1000, 2), error_type=type(exc).__name__)
            raise
        log_event("workflow.step.completed", workflow_step=name,
                  result_count=len(result.get("email_results", [])),
                  duration_ms=round((perf_counter() - started) * 1000, 2))
        return result
    return observed


def build_graph(
    email_provider,
    task_provider,
    calendar_provider=None,
    *,
    analyzer=analyze_email,
    email_filter_classifier=classify_email_filter,
    email_triage_classifier=triage_emails,
    model_turn=agent_turn,
    max_tool_calls: int = MAX_TOOL_CALLS,
):
    """Build the bounded Gemini-tool/LangGraph workflow for one local user."""
    toolset = EmailAgentTools(email_provider, task_provider, calendar_provider,
                              analyzer=analyzer, email_filter_classifier=email_filter_classifier,
                              email_triage_classifier=email_triage_classifier)

    def initialize(state: EmailAgentState):
        message = state.get("message", "")
        messages = [types.Content(role="user", parts=[types.Part.from_text(text=message)])]
        filter_id = state.get("filter_id")
        preset = PRESET_TOOL_CALLS.get(filter_id)
        if preset:
            from app.services.ai_service import AgentToolCall
            return {"messages": messages, "tool_calls": [AgentToolCall(name=preset[0], arguments=preset[1])],
                    "tool_call_count": 0, "email_results": [], "email_reviews": []}
        return {"messages": messages, "tool_calls": [], "tool_call_count": 0,
                "email_results": [], "email_reviews": []}

    def run_agent(state: EmailAgentState):
        enabled = state.get("tool_call_count", 0) < max_tool_calls
        instruction = build_agent_system_prompt(current_email_id=state.get("current_email_id"),
                                                selected_email_id=state.get("selected_email_id"))
        try:
            turn = model_turn(state.get("messages", []), TOOL_DECLARATIONS, instruction, tools_enabled=enabled)
        except AIServiceConfigurationError:
            return {"response": "Chat needs Gemini. Set GEMINI_API_KEY and try again.", "tool_calls": []}
        except Exception as exc:
            logger.warning("Gemini agent turn failed (error_type=%s, status_code=%s, api_status=%s)",
                           type(exc).__name__, getattr(exc, "code", None), getattr(exc, "status", None))
            return {"response": "I couldn't complete that request right now. Please try again.", "tool_calls": []}

        messages = list(state.get("messages", []))
        if turn.model_content is not None:
            messages.append(turn.model_content)
        if turn.tool_calls:
            if not enabled:
                return {"messages": messages, "response": "I reached the safe limit for this request. Please try a smaller or more specific request.", "tool_calls": []}
            return {"messages": messages, "tool_calls": turn.tool_calls, "response": ""}
        answer = turn.text or "I couldn't find a useful answer for that request. Could you rephrase it?"
        return {"messages": messages, "response": answer, "tool_calls": []}

    def execute_tools(state: EmailAgentState):
        calls = state.get("tool_calls", [])
        if not calls:
            return {"response": "I couldn't complete that request safely."}
        messages = list(state.get("messages", []))
        results = list(state.get("email_results", []))
        reviews = list(state.get("email_reviews", []))
        current_id = state.get("current_email_id")
        clear_current = False
        count = state.get("tool_call_count", 0)
        for call in calls:
            if count >= max_tool_calls:
                return {"messages": messages, "tool_calls": [], "response": "I reached the safe limit for this request. Please try a smaller or more specific request.",
                        "email_results": results, "email_reviews": reviews, "current_email_id": current_id}
            outcome = toolset.execute(call.name, call.arguments, state)
            count += 1
            messages.append(types.Content(role="tool", parts=[types.Part.from_function_response(
                name=call.name, response=outcome.data)]))
            if outcome.emails or outcome.clear_current_email:
                results = outcome.emails
                reviews = outcome.reviews
                current_id = outcome.current_email_id
                clear_current = outcome.clear_current_email
            elif outcome.reviews:
                reviews = outcome.reviews
            if outcome.current_email_id:
                current_id = outcome.current_email_id
                clear_current = False
        return {"messages": messages, "tool_calls": [], "tool_call_count": count,
                "email_results": results, "email_reviews": reviews,
                "current_email_id": current_id, "clear_current_email": clear_current}

    def next_step(state: EmailAgentState):
        if state.get("tool_calls"):
            return "tools"
        return END

    def after_initialize(state: EmailAgentState):
        return "tools" if state.get("tool_calls") else "agent"

    graph = StateGraph(EmailAgentState)
    graph.add_node("initialize", _observe_node("initialize", initialize))
    graph.add_node("agent", _observe_node("agent", run_agent))
    graph.add_node("tools", _observe_node("tools", execute_tools))
    graph.add_edge(START, "initialize")
    graph.add_conditional_edges("initialize", after_initialize, {"agent": "agent", "tools": "tools"})
    graph.add_conditional_edges("agent", next_step, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()
