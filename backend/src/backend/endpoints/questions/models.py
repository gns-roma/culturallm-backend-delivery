from typing import Literal
from pydantic import BaseModel



class QuestionValues(BaseModel):
    question: str
    topic: str

class QuestionBasic(BaseModel):
    id: int
    question: str
    topic: str

class QuestionEvaluation(BaseModel):
    id: int 
    llm_id: int
    question_id: int
    cultural_specificity: int
    cultural_specificity_notes: str | None = None
    coherence_qt: bool | None = None    

