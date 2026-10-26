from pydantic import BaseModel, Field


class Meeting(BaseModel):
    id: str
    title: str = Field(min_length=1, max_length=300)
    start: str
    end: str | None = None
    all_day: bool = False
    location: str | None = None
    url: str | None = None
