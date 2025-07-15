from pydantic import BaseModel, Field

class QuestionGenerationRequest(BaseModel):
    argument: str


class QuestionGenerationResponse(BaseModel):
    question_generated: str
    raw_llm_output: str


class EvalValidityRequest(BaseModel):
    question: str
    answer: str


class EvalResponse(BaseModel):
    score: int # punteggio da 1 a 5
    feedback: str # spiegazione della valutazione
    raw_llm_output: str # output grezzo del modello


class EvalCulturalRequest(BaseModel):
    question: str  # Argomento da valutare


class EvalCoherenceQTRequest(BaseModel):
    question: str # Domanda da valutare
    theme: str # Tema di riferimento4


class EvalCoherenceQARequest(BaseModel):
    question: str # Domanda da valutare
    answer: str # Risposta da valutare


class AnswerRequest(BaseModel):
    question: str  # Domanda a cui rispondere
    level: int    # Livello di dettaglio (1-5)


class AnswerResponse(BaseModel):
    answer: str  # Risposta del modello 
    raw_llm_output: str    # Output grezzo del modello


class HumanizeRequest(BaseModel):
    llm_response: str = Field(..., description="La risposta originale dell'LLM da umanizzare.")
    level: int = Field(..., ge=1, le=4, description="Livello di umanizzazione (1=min, 4=max).")


class HumanizeResponse(BaseModel):
    humanized_response: str
    raw_llm_output: str # Per debug o analisi dell'output grezzo