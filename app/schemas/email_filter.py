from pydantic import BaseModel, Field


class EmailFilterClassification(BaseModel):
    """1-based positions of email excerpts matching a semantic filter."""

    matching_indices: list[int] = Field(default_factory=list, max_length=20)
