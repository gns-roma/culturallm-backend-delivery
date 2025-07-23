from typing import Annotated, Literal, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
import mariadb
import logging
from endpoints.questions.models import QuestionValues, QuestionBasic
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user, get_current_user_id
from endpoints.validate.models import RatingRequest
from endpoints.questions.questions_nlp import background_evaluation_pipeline
import asyncio


router = APIRouter(prefix="/questions", tags=["questions"])
logger = logging.getLogger("app")

@router.post("/")
async def submit_question(
    data: QuestionValues,
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> Response:
    
    if type == "human" and current_user is None:
        return Response(status_code=401, content="Errore: l'utente deve essere loggato per inserire una domanda")
    
    logging.info(f"domanda: {data.question} autore (username): {current_user}")
    
    username = current_user if type == "human" else None
    
    user_id = get_current_user_id(username, db)

    insert_query = "INSERT INTO questions (question, topic, type, user_id) VALUES (?, ?, ?, ?)"
    params = (data.question, data.topic, type, user_id)
    # ritorna all'id della domanda
    question_id = execute_query(db, insert_query, params, fetch=False)
    
    if question_id is None:
        logger.info(f"question_id={question_id} non valido")
        raise HTTPException(status_code=500, detail="Errore interno: question_id non valido")
    
    # Lancia la task asincrona senza bloccare
    asyncio.create_task(
        background_evaluation_pipeline(data.question, data.topic, db, question_id)
    )

    return Response(status_code=201)


@router.get("/qa_to_validate")
def get_single_answer_to_question(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human",
) -> RatingRequest:
    
    """
    Restituisce UNA tupla domanda, risposta, topic che l'utente
    corrente non ha creato né già valutato.
    Preferisce la risposta con il minor numero di rating.
    """
    if type == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Errore: l'utente deve essere loggato",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = current_user
    user_id = get_current_user_id(username, db)
    
    select_query = """
    SELECT a.id AS answer_id, a.question_id AS question_id, a.answer, q.question, q.topic
    FROM answers AS a INNER JOIN questions AS q ON a.question_id = q.id LEFT JOIN ratings AS r ON a.id = r.answer_id
    WHERE (a.user_id IS NULL OR a.user_id != ?)
    AND NOT EXISTS (
        SELECT 1
        FROM ratings AS r_check
        WHERE r_check.answer_id = a.id AND r_check.user_id = ?)
    GROUP BY a.id, a.question_id, q.question, a.answer, q.topic
    ORDER BY COUNT(r.id) ASC, RAND()
    LIMIT 1;"""
    
    params = (user_id, user_id)

    row = execute_query(db, select_query, params, fetch=False, fetchone=True, dict=True)
    
    if not row:
        raise HTTPException(status_code=404, detail="Non ci sono risposte adatte a quanto pare...")

    return RatingRequest(**row)




@router.get("/random/to_answer")
def get_random_question_to_answer(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> QuestionBasic:
    """
    Ritorna ad una domanda a cui l'utente non ha mai risposto, anche se è stata scritta dall'utente stesso
    """
    if current_user is None and type == "human":
        raise HTTPException(
            status_code=401,
            detail="Errore: L'utente deve aver eseguito il login per poter rispondere ad una domanda.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = current_user if type == "human" else ""

    user_id = get_current_user_id(username, db)

    # Ritorna una domanda casuale a cui l'utente non ha ancora risposto
    select_query = """
    SELECT q.id, q.question, q.topic
    FROM questions q 
    WHERE q.id NOT IN (
        SELECT a.question_id
        FROM answers a
        WHERE a.user_id = ?
    )
    ORDER BY RAND()
    LIMIT 1
    """
    
    params = (user_id,)
    row = execute_query(db, select_query, params, fetchone=True, dict=True)

    if row is None:
        raise HTTPException(status_code=404, detail="Nessuna domanda disponibile.")
    return QuestionBasic(**row)



