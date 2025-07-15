import httpx
import os
from db.mariadb import db_connection, execute_query
from typing import Annotated,  Optional
from fastapi import Depends, HTTPException
import mariadb

BASE_URL = "http://nlp:8004"

async def evaluate_cultural_background(
    question: str, 
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    question_id: int
):
    url = f"{BASE_URL}/evaluate_cultural"
    headers = {
        "x-access-key": os.getenv("GREEN_CULTURAL_ACCESS_KEY", "")  # caricato da .env
    }
    payload = {"question": question}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            score = data.get("score")
            feedback = data.get("feedback")

       
            update_query = """
                UPDATE questions SET cultural_specificity = ?, cultural_specificity_notes = ?
                WHERE id = ?
            """
            execute_query(db, update_query, (score, feedback, question_id), fetch=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore endpoint nlp: {e}")



async def answer_question(question_id: int, question: str, level: int, 
                            db: Annotated[mariadb.Connection, Depends(db_connection)]):
    url = f"{BASE_URL}/answer"
    headers = {
        "x-access-key": os.getenv("CYAN_ACCESS_KEY", "")  # caricato da .env
    }
    payload = {"question": question, "level": level}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            answer = data.get("answer")
        insert_query = """
            INSERT INTO answers (answer, question_id, type)
            VALUES (?, ?, 'llm')
        """
        execute_query(db, insert_query, (answer, question_id), fetch=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore endpoint nlp: {e}")
    

async def evaluate_coherence_qt(
        question_id: int,
        question: str,
        theme: str,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    url = f"{BASE_URL}/evaluate_coherence_qt"
    headers = {
        "x-access-key": os.getenv("GREEN_COHERENCE_QT_ACCESS_KEY", "")  # caricato da .env
    }
    payload = {
        "question": question,
        "theme": theme
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            print(f"Coherence evaluation result: {data}", flush=True)

            update_query = """
                UPDATE questions SET coherence_qt = ?
                WHERE id = ?
            """
            execute_query(db, update_query, (data, question_id), fetch=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore endpoint nlp: {e}")
