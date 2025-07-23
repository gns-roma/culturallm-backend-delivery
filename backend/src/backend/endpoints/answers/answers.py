from fastapi import APIRouter, BackgroundTasks, Depends, Response, HTTPException
from typing import Annotated, Literal, Optional, List
import mariadb
from endpoints.answers.answers_nlp import background_evaluation_pipeline
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user, get_current_user_id
from endpoints.answers.models import AnswerValues
import asyncio
import logging


router = APIRouter(prefix="/answers", tags=["answers"])
logger = logging.getLogger("app")


@router.post("/")
async def submit_answer(
    data : AnswerValues,
    background_tasks: BackgroundTasks,
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> Response:
    """
    Inserisci una risposta ad una domanda 
    """

    if type == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Errore: l'utente deve essere loggato per poter rispondere ad una domanda.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = current_user if type == "human" else ""
    if username is None:
        username = ""
    
    user_id = get_current_user_id(username, db)

    insert_query = """
        INSERT INTO answers (question_id, user_id, type, answer) 
        VALUES (?, ?, ?, ?)
    """
    params = (data.question_id, user_id, type, data.answer)

    answer_id = execute_query(db, insert_query, params, fetch=False)
    
    if not answer_id:
        logger.info(f"answer_id={answer_id}")
        raise HTTPException(status_code=500, detail="Errore interno durante l'inserimento della risposta")

    # Lancia la task asincrona senza bloccare
    asyncio.create_task(
        background_evaluation_pipeline(data.question_id, data.answer, answer_id, db)
    )

    return Response(status_code=201)


