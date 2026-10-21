from fastapi import APIRouter
from collections import OrderedDict
from app.schemas.agent import AgentChatRequest, AgentChatResponse


def build_router(graph):
    router = APIRouter(prefix="/agent", tags=["agent"])
    current_emails: OrderedDict[str, str] = OrderedDict()

    @router.post("/chat", response_model=AgentChatResponse)
    def chat(request: AgentChatRequest):
        result = graph.invoke({
            "message": request.message,
            "current_email_id": current_emails.get(request.thread_id),
        })
        current_email_id = result.get("current_email_id")
        if current_email_id:
            current_emails[request.thread_id] = current_email_id
            current_emails.move_to_end(request.thread_id)
            if len(current_emails) > 256:
                current_emails.popitem(last=False)
        elif request.thread_id in current_emails and "not found" in result.get("response", "").lower():
            current_emails.pop(request.thread_id, None)
        return AgentChatResponse(
            thread_id=request.thread_id,
            response=result.get("response", "I couldn't complete that request."),
            current_email_id=current_email_id,
        )

    return router
