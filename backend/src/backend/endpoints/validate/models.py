from pydantic import BaseModel, Field

class RatingRequest(BaseModel):
    question: str
    question_id: int
    answer: str
    answer_id: int
    topic: str


class RatingValues(BaseModel):
    #Non c'è bisogno di fare check del valore del rating perchè l'idea è che selezioni solo 1 valore tra 1 e 5
    rating: int
    answer_id: int
    question_id: int
    flag_ia: bool

