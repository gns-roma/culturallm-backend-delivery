from typing import Literal
from pydantic import BaseModel

class AnswerValues(BaseModel):
    question_id: int
    answer: str


class Answer(BaseModel):
    id: int
    type: Literal["human", "llm"]
    username: str | None
    question_id : int
    answer: str