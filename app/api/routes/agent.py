from fastapi import APIRouter
from collections import OrderedDict
from app.schemas.agent import AgentChatRequest, AgentChatResponse


EMAIL_FILTER_IDS = {"important_unread", "escalated_unread", "customer_unread"}


def build_router(graph):
    router = APIRouter(prefix="/agent", tags=["agent"])
    current_emails: OrderedDict[str, str] = OrderedDict()

    @router.post("/chat", response_model=AgentChatResponse)
    def chat(request: AgentChatRequest):
        result = graph.invoke({
            "message": request.message,
            "current_email_id": current_emails.get(request.thread_id),
            "filter_id": request.filter_id,
            "selected_email_id": request.selected_email_id,
        })
        current_email_id = result.get("current_email_id")
        if current_email_id:
            current_emails[request.thread_id] = current_email_id
            current_emails.move_to_end(request.thread_id)
            if len(current_emails) > 256:
                current_emails.popitem(last=False)
        elif request.filter_id in EMAIL_FILTER_IDS or result.get("clear_current_email"):
            current_emails.pop(request.thread_id, None)
        elif request.thread_id in current_emails and "not found" in result.get("response", "").lower():
            current_emails.pop(request.thread_id, None)
        reviews_by_email_id = {
            review["email_id"]: review
            for review in result.get("email_reviews", [])
            if review.get("email_id")
        }
        return AgentChatResponse(
            thread_id=request.thread_id,
            response=result.get("response", "I couldn't complete that request."),
            current_email_id=current_email_id,
            email_options=[
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": str(email.sender),
                    "received_at": email.received_at,
                    "summary": reviews_by_email_id.get(email.id, {}).get("summary"),
                    "priority": reviews_by_email_id.get(email.id, {}).get("priority"),
                    "requires_action": reviews_by_email_id.get(email.id, {}).get("requires_action"),
                    "requires_attention": reviews_by_email_id.get(email.id, {}).get("requires_attention"),
                    "action_items": reviews_by_email_id.get(email.id, {}).get("action_items", []),
                }
                for email in result.get("email_results", [])
            ],
        )

    return router
