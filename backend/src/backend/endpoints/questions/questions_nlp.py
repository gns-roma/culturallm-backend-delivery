import asyncio
import httpx
import os
from db.mariadb import db_connection, execute_query
from typing import Annotated,  Optional
from fastapi import Depends, HTTPException
import mariadb
import logging

NLP_PORT = int(os.getenv("NLP_PORT", 8071))
NLP_IP = os.getenv("NLP_IP", "143.198.37.78")

BASE_URL = f"http://{NLP_IP}:{NLP_PORT}"

TEST_LLM_ID = 1

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



async def evaluate_cultural_background(
    question: str, 
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    question_id: int
):
    
    url = f"{BASE_URL}/green_cultural"
    payload = {"question": question}

    # aspettiamo che la richiesta termini
    resp = await post_to_nlp(url, payload)
        
    data = resp.json()
    
    # cultural_specificity nel DB è l'equivalente di score
    cultural_specificity = data.get("score")
    # cultural_specificity_notes nel DB è l'equivalente di feedback
    cultural_specificity_notes = data.get("feedback")

    insert_query = """
        INSERT INTO questions_evaluation (question_id, llm_id, cultural_specificity, cultural_specificity_notes) VALUES (?, ?, ?, ?)
    """

    execute_query(db, insert_query, (question_id, TEST_LLM_ID, cultural_specificity, cultural_specificity_notes), fetch=False)



async def answer_question(question_id: int, question: str, level: int, 
                            db: Annotated[mariadb.Connection, Depends(db_connection)], humanize=True):
    url = f"{BASE_URL}/cyan"
    payload = {"argomento": question, "livello": level}

    resp = await post_to_nlp(url, payload)

    data = resp.json()
    answer = data.get("risposta")

    # inseriamo la rirsposta su hunanize 
    if (humanize):
        logging.info(f"Sto umanizzando la risposta alla domanda con id: {question_id}")
        huamnized_answer = await humanize_answer(answer)
        logging.info(f"Ecco la risposta prima:\n{answer}\ndopo:{huamnized_answer}")
        answer = huamnized_answer
    
    insert_query = """
        INSERT INTO answers (llm_id, question_id, answer, type)
        VALUES (?, ?, ?, 'llm')
    """
    execute_query(db, insert_query, (TEST_LLM_ID, question_id, answer), fetch=False)



async def humanize_answer(llm_response: str, humanization_level: int = 1) -> str:
    url = f"{BASE_URL}/magenta"
    payload = {"llm_response": llm_response, "level": humanization_level}

    resp = await post_to_nlp(url, payload)

    data = resp.json()
    humanized_response = data.get("humanized_response")

    return humanized_response
    

async def evaluate_coherence_qt(
        question_id: int,
        question: str,
        theme: str,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    url = f"{BASE_URL}/green_coherence_QT"
    payload = {
        "question": question,
        "theme": theme
    }

    resp = await post_to_nlp(url, payload)
    
    data = resp.json()
    value = True if data.get("bool") == "Vero" else False

    logging.info(f"question=[id:{question_id} text:{question}]\nCoherence evaluation result: {data}")

    # questa update_query va in realtà eseguita su 
    #  questions_evaluation

    update_query = """
        UPDATE questions_evaluation SET coherence_qt = ?
        WHERE id = ?
    """

    execute_query(db, update_query, (value, question_id), fetch=False)


async def background_evaluation_pipeline(question: str, topic: str, db: mariadb.Connection, question_id: int):

    await evaluate_cultural_background(question, db, question_id)
    await evaluate_coherence_qt(question_id, question, topic, db)

    logging.info("Eseguiti i due endpoint di nlp")

    query_evaluate = """
        SELECT cultural_specificity, coherence_qt
        FROM questions_evaluation
        WHERE id = ?
    """
    params_evaluate = (question_id,)
    
    row = execute_query(db, query_evaluate, params_evaluate, fetchone=True, dict=True)

    # la risposta alla domanda viene generata solamente se certi criteri sono rispettati
    if row and row['cultural_specificity'] >= 4 and row['coherence_qt'] == 1:
        await answer_question(question_id, question, 1, db)

