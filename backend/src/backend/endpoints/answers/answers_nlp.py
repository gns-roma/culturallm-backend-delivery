import asyncio
import os
from fastapi import Depends, HTTPException
import httpx
from typing_extensions import Annotated
import mariadb
from db.mariadb import db_connection, execute_query
import logging

NLP_PORT = int(os.getenv("NLP_PORT", 8071))
NLP_IP = os.getenv("NLP_IP", "143.198.37.78")

BASE_URL = f"http://{NLP_IP}:{NLP_PORT}"

TEST_LLM_ID = 1
logger = logging.getLogger("app")

semaphore = asyncio.Semaphore(1)

async def post_to_nlp(url: str, payload: dict[str, str]):
    resp = None

    try:
        async with semaphore:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=300.0)
                resp.raise_for_status()

    except httpx.HTTPStatusError as e:
         raise HTTPException(status_code=e.response.status_code, detail=f"Errore HTTP dal servizio LLM: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Errore di rete contattando il servizio LLM: {e}")
    
    return resp


async def evaluate_validity(
        answer: str,
        question: str,
        answer_id: int,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    """
    Evaluate the validity of an answer using the NLP service.
    """
    url = f"{BASE_URL}/green_validity"
    payload = {
        "question": question,
        "answer": answer
    }

    resp = await post_to_nlp(url, payload)

    data = resp.json()
    # score equivalente a validity nel db
    validity = data.get("score")
    # feedback equivalente a valdiity_notes nel db
    validity_notes = data.get("feedback")


    # questa query deve diventare una insert perchè
    # c'è answers_evaluation
    #
    # update_query = """
    #     UPDATE answers SET validity = ?, validity_notes = ?
    #     WHERE id = ?
    # """

    insert_query = """
        INSERT INTO answers_evaluation (answer_id, llm_id, validity, validity_notes) VALUES (?, ?, ?, ?)
    """

    execute_query(db, insert_query, (answer_id, TEST_LLM_ID, validity, validity_notes), fetch=False)

    

async def evaluate_coherence_qa(
        answer: str,
        question: str,
        answer_id: int,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    url = f"{BASE_URL}/green_coherence_QA"
    payload = {
        "question": question,
        "answer": answer
    }

    resp = await post_to_nlp(url, payload)

    data = resp.json()
    value = True if data.get("bool") == "Vero" else False

    logger.info(f"[answer=id:{answer_id} text:{answer}] question={question}\nCoherence evaluation result: {data}")

    # rimane sempre update ma cambia la tabella su cui viene eseguito
    # update_query = """
    #     UPDATE answers SET coherence_qa = ?
    #     WHERE id = ?
    # """

    update_query = """
        UPDATE answers_evaluation SET coherence_qa = ?
        WHERE id = ?
    """
    
    execute_query(db, update_query, (value, answer_id), fetch=False)




async def background_evaluation_pipeline(question_id: int, 
                                         answer: str,
                                         answer_id: str, 
                                         db: Annotated[mariadb.Connection, Depends(db_connection)]):

    ##Prendi il testo della domanda
    question_query = """
        SELECT question
        FROM questions 
        WHERE id = ?
    """
    
    question_check = execute_query(db, question_query, (question_id,), fetchone=True, dict=True)
    if not question_check:
        raise HTTPException(status_code=404, detail="Domanda non trovata")
    
    question = question_check["question"] 

    await evaluate_validity(answer, question, int(answer_id), db)
    await evaluate_coherence_qa(answer, question, int(answer_id), db)