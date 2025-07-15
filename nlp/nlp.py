###########################################################
# nlp.py
# Codice tratto in gran parte dalla repo dei ragazzi di NLP
# e adattato per usare gli Agent Platform di DigitalOcean
###########################################################

import re
from os import getenv
from fastapi import FastAPI, HTTPException, Header
from httpx import AsyncClient, ReadTimeout
from pydantic import BaseModel

from models import *

app = FastAPI()

@app.get("/")
def read_root():
    pass


def headers(access_key: str) -> dict:
    return{
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_key}"
    }


def payload(message: str) -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False,
        "include_functions_info": False,
        "include_retrieval_info": False,
        "include_guardrails_info": False
    }


@app.post("/generate_question", tags=["question_generation"])
async def generate_question(
    request: QuestionGenerationRequest,
    x_access_key: str = Header(...)
) -> QuestionGenerationResponse:
    """
    Generate a question based on the provided topic.
    """
    YELLOW_ENDPOINT_URL = getenv("YELLOW_ENDPOINT_URL")

    if not YELLOW_ENDPOINT_URL:
        raise ValueError("Environment variable YELLOW_ENDPOINT_URL must be set.")

    async with AsyncClient() as client:
        response = await client.post(
            url=f"{YELLOW_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Argomento: {request.argument}")
        )
        response.raise_for_status()
        out = response.json()["choices"][0]["message"]["content"].strip()

        return QuestionGenerationResponse(
            question_generated=out,
            raw_llm_output=out
        )
    

@app.post("/evaluate_validity", tags=["evaluate"])
async def evaluate_validity(
    request: EvalValidityRequest,
    x_access_key: str = Header(...)
) -> EvalResponse:
    """
    Evaluate the validity of an answer to a question.
    """
    GREEN_VALIDITY_ENDPOINT_URL = getenv("GREEN_VALIDITY_ENDPOINT_URL")

    if not GREEN_VALIDITY_ENDPOINT_URL:
        raise ValueError("Environment variable GREEN_VALIDITY_ENDPOINT_URL must be set.")
    
    async with AsyncClient() as client:
        response = await client.post(
            url=f"{GREEN_VALIDITY_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Domanda: {request.question}\nRisposta: {request.answer}")
        )
        response.raise_for_status()

        out = response.json()["choices"][0]["message"]["content"].strip()
        out = out.replace("<newline>", "\n")

        print(f"Raw LLM output: {out}", flush=True)

        feedback_match = re.search(r"Feedback:\s*(.*?)\s*\n", out, re.IGNORECASE | re.DOTALL)
        feedback = feedback_match.group(1) if feedback_match else ""

        nums = re.findall(r"\d+", out)
        if not nums:
            raise HTTPException(status_code=500, detail=f"Nessun numero trovato nell'output: {out}")
        score = int(nums[-1])
        if score < 1 or score > 5:
            raise HTTPException(status_code=500, detail=f"Punteggio fuori range: {score}")
        
        return EvalResponse(
            score=score,
            feedback=feedback,
            raw_llm_output=out
        )
    

@app.post("/evaluate_cultural", tags=["evaluate"])
async def evaluate_cultural(
    request: EvalCulturalRequest,
    x_access_key: str = Header(...)
) -> EvalResponse:
    """
    Evaluate the cultural relevance of a question.
    """
    GREEN_CULTURAL_ENDPOINT_URL = getenv("GREEN_CULTURAL_ENDPOINT_URL")

    if not GREEN_CULTURAL_ENDPOINT_URL:
        raise ValueError("Environment variable GREEN_CULTURAL_ENDPOINT_URL must be set.")
    
    async with AsyncClient() as client:
        response = await client.post(
            url=f"{GREEN_CULTURAL_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Domanda: {request.question}")
        )
        response.raise_for_status()

        out = response.json()["choices"][0]["message"]["content"].strip()
        out = out.replace("<newline>", "\n")

        print(f"Raw LLM output: {out}", flush=True)

        feedback_match = re.search(r"Feedback:\s*(.*?)\s*\n", out, re.IGNORECASE | re.DOTALL)
        feedback = feedback_match.group(1) if feedback_match else ""

        nums = re.findall(r"\d+", out)
        if not nums:
            raise HTTPException(status_code=500, detail=f"Nessun numero trovato nell'output: {out}")
        score = int(nums[-1])
        if score < 0 or score > 10:
            raise HTTPException(status_code=500, detail=f"Punteggio fuori range: {score}")
        
        return EvalResponse(
            score=score,
            feedback=feedback,
            raw_llm_output=out
        )
    

@app.post("/evaluate_coherence_qt", tags=["evaluate"])
async def evaluate_coherence_qt(
    request: EvalCoherenceQTRequest,
    x_access_key: str = Header(...)
) -> bool:
    """
    Evaluate the coherence between question and theme provided.
    """
    GREEN_COHERENCE_QT_ENDPOINT_URL = getenv("GREEN_COHERENCE_QT_ENDPOINT_URL")

    if not GREEN_COHERENCE_QT_ENDPOINT_URL:
        raise ValueError("Environment variable GREEN_COHERENCE_QT_ENDPOINT_URL must be set.")
    
    async with AsyncClient() as client:
        response = await client.post(
            url=f"{GREEN_COHERENCE_QT_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Domanda: {request.question}\nTema: {request.theme}")
        )
        response.raise_for_status()

        out = response.json()["choices"][0]["message"]["content"].strip()

        print(f"Raw LLM output: {out}", flush=True)

        bool_match = re.search(r"\b(Vero|Falso)\b", out, re.IGNORECASE)
        
        if not bool_match:
            raise HTTPException(
                status_code=500, 
                detail=f"Output non valido: '{out}'. Deve essere 'Vero' o 'Falso'"
            )
            
        bool_result = bool_match.group(1)
        
        if bool_result == "Vero":
            return True
        else:
            return False
        

@app.post("/evaluate_coherence_qa", tags=["evaluate"])
async def evaluate_coherence_qa(
    request: EvalCoherenceQARequest,
    x_access_key: str = Header(...)
) -> bool:
    """
    Evaluate the coherence between question and answer provided.
    """
    GREEN_COHERENCE_QA_ENDPOINT_URL = getenv("GREEN_COHERENCE_QA_ENDPOINT_URL")

    if not GREEN_COHERENCE_QA_ENDPOINT_URL:
        raise ValueError("Environment variables GREEN_COHERENCE_QA_ENDPOINT_URL must be set.")
    
    async with AsyncClient() as client:
        response = await client.post(
            url=f"{GREEN_COHERENCE_QA_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Domanda: {request.question}\nRisposta: {request.answer}")
        )
        response.raise_for_status()

        out = response.json()["choices"][0]["message"]["content"].strip()

        bool_match = re.search(r"\b(Vero|Falso)\b", out, re.IGNORECASE)
        
        if not bool_match:
            raise HTTPException(
                status_code=500, 
                detail=f"Output non valido: '{out}'. Deve essere 'Vero' o 'Falso'"
            )
            
        bool_result = bool_match.group(1)
        
        if bool_result == "Vero":
            return True
        else:
            return False
        

@app.post("/answer", tags=["answer"])
async def answer(
    request: AnswerRequest,
    x_access_key: str = Header(...)
) -> AnswerResponse:
    """
    Answer to the given question, following the given level.
    """
    CYAN_ENDPOINT_URL = getenv("CYAN_ENDPOINT_URL")

    if not CYAN_ENDPOINT_URL:
        raise ValueError("Environment variables CYAN_ENDPOINT_URL must be set.")
    
    try:
        async with AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url=f"{CYAN_ENDPOINT_URL}/api/v1/chat/completions",
                headers=headers(x_access_key),
                json=payload(f"Argomento: {request.question}\nLivello: {request.level}")
            )
            response.raise_for_status()

            out = response.json()["choices"][0]["message"]["content"].strip()

            answer_match = re.search(r"Risposta:\s*(.*?)\s*\n", out, re.IGNORECASE | re.DOTALL)
            answer = answer_match.group(1) if answer_match else out

            return AnswerResponse(
                answer=answer,
                raw_llm_output=out
            )
    except ReadTimeout:
        raise HTTPException(status_code=504, detail="Timeout durante la risposta del modello LLM.")


@app.post("/humanize", tags=["humanize"])
async def humanize(
    request: HumanizeRequest,
    x_access_key: str = Header(...)
) -> HumanizeResponse:
    """
    Humanize the given text.
    """
    MAGENTA_ENDPOINT_URL = getenv("MAGENTA_ENDPOINT_URL")

    if not MAGENTA_ENDPOINT_URL:
        raise ValueError("Environment variable MAGENTA_ENDPOINT_URL must be set.")
    
    async with AsyncClient() as client:
        response = await client.post(
            url=f"{MAGENTA_ENDPOINT_URL}/api/v1/chat/completions",
            headers=headers(x_access_key),
            json=payload(f"Risposta LLM orginale: {request.llm_response}\nLivello di umanizzazione: {request.level}")
        )
        response.raise_for_status()

        out = response.json()["choices"][0]["message"]["content"].strip()

        return HumanizeResponse(
            humanized_response=out,
            raw_llm_output=out
        )