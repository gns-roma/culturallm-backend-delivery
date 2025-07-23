from pydantic import BaseModel

class Report(BaseModel):
    report: str | None = None
    question_id: int | None = None
    answer_id: int | None = None