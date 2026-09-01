from pydantic import BaseModel
from typing import Literal

class AICategory(BaseModel):
    main: str
    sub_category: str | None = None
    group: str | None = None

class AIAnalysis(BaseModel):
    summary: str
    category: AICategory
    priority: Literal["Critical", "High", "Medium", "Low"]
    sentiment: Literal["Positive", "Neutral", "Negative"]
    requires_action: bool
    requires_attention: bool
    action_items: list[str]