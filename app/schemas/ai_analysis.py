from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator


class AICategory(BaseModel):
    main: str = Field(min_length=1, max_length=100)
    sub_category: str | None = None
    group: str | None = None


class AIAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)
    category: AICategory
    priority: Literal["Critical", "High", "Medium", "Low"]
    sentiment: Literal["Positive", "Neutral", "Negative"]
    requires_action: bool
    requires_attention: bool
    action_items: list[Annotated[str, Field(min_length=1, max_length=300)]] = Field(max_length=50)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value):
        if isinstance(value, str):
            return {option.lower(): option for option in ("Critical", "High", "Medium", "Low")}.get(value.strip().lower(), value)
        return value

    @field_validator("action_items", mode="before")
    @classmethod
    def normalize_action_items(cls, value):
        if not isinstance(value, list):
            return value
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
