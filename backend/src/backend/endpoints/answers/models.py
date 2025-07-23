from typing import Literal
from pydantic import BaseModel

class AnswerValues(BaseModel):
    question_id: int
    answer: str


class AnswerBasic(BaseModel):
    id: int
    topic : str
    question : str
    answer: str
    score: int


class AnswerEvaluations(BaseModel):
    id: int 
    llm_id: int
    answer_id: int
    validity: int
    validity_notes: str | None = None
    coherence_qa: bool | None = None    