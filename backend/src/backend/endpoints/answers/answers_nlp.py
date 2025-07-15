import os
from fastapi import Depends, HTTPException
import httpx
from typing_extensions import Annotated

import mariadb

from db.mariadb import db_connection, execute_query


BASE_URL = "http://nlp:8004"


async def evaluate_validity(
        answer: str,
        question: str,
        answer_id: int,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    """
    Evaluate the validity of an answer using the NLP service.
    """
    url = f"{BASE_URL}/evaluate_validity"
    headers = {
        "x-access-key": os.getenv("GREEN_VALIDITY_ACCESS_KEY", "")
    }
    payload = {
        "question": question,
        "answer": answer
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            score = data.get("score")
            feedback = data.get("feedback")

            update_query = """
                UPDATE answers SET validity = ?, validity_notes = ?
                WHERE id = ?
            """
            execute_query(db, update_query, (score, feedback, answer_id), fetch=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore endpoint nlp: {e}")
    

async def evaluate_coherence_qa(
        answer: str,
        question: str,
        answer_id: int,
        db: Annotated[mariadb.Connection, Depends(db_connection)]
):
    url = f"{BASE_URL}/evaluate_coherence_qa"
    headers = {
        "x-access-key": os.getenv("GREEN_COHERENCE_QA_ACCESS_KEY", "")  # caricato da .env
    }
    payload = {
        "question": question,
        "answer": answer
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            print(f"Coherence evaluation result: {data}", flush=True)

            update_query = """
                UPDATE answers SET coherence_qa = ?
                WHERE id = ?
            """
            execute_query(db, update_query, (data, answer_id), fetch=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore endpoint nlp: {e}")