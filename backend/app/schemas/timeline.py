from pydantic import BaseModel


class TimelineItem(BaseModel):
    type: str
    title: str
    body: str
    time: str
