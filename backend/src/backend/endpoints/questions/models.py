from typing import Literal
from pydantic import BaseModel



class QuestionValues(BaseModel):
    question: str
    topic: str


class Question(BaseModel):
    id: int
    type: Literal["human", "llm"]
    username: str | None
    question: str
    topic: str
    cultural_specificity: int | None = None
    cultural_specificity_notes: str | None = None
