from fastapi import APIRouter, BackgroundTasks, Depends, Response, HTTPException
from typing import Annotated, Literal, Optional, List
from fastapi.routing import APIRoute
import mariadb
from endpoints.answers.answers_nlp import evaluate_coherence_qa, evaluate_validity
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user
from endpoints.validate.models import Rating
from endpoints.answers.models import AnswerValues


router = APIRouter(prefix="/answers", tags=["answers"])

@router.post("/")
def submit_answer(
    data : AnswerValues,
    background_tasks: BackgroundTasks,
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None,
    type: Literal["human", "llm"] = "human"
) -> Response:
    """
    Submit an answer to a question.
    """
    if type == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in to answer a question.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = current_user if type == "human" else None

    # Controllo domanda esistente
    question_query = """
        SELECT id, question
        FROM questions 
        WHERE id = ?
    """
    question_check = execute_query(db, question_query, (data.question_id,), fetchone=True, dict=True)
    print(question_check, flush=True)
    print(f"Question check for id={data.question_id}: {question_check}")
    if not question_check:
        raise HTTPException(status_code=404, detail="Domanda non trovata")
    
    query_user = """
        SELECT id
        FROM users 
        WHERE username = ?
    """
    params_user = (username,) if username else (None,)
    try:
        user_check = execute_query(db, query_user, params_user, fetchone=True, dict=True)
    except Exception as e:
        print(f"Errore durante l'inserimento risposta: {e}")
        raise HTTPException(status_code=500, detail="Errore interno durante l'inserimento della risposta")

    user_id = user_check['id'] if user_check else None

    insert_query = """
        INSERT INTO answers (question_id, user_id, type, answer) 
        VALUES (?, ?, ?, ?)
    """
    params = (data.question_id, user_id, type, data.answer)

    try:
        answer_id = execute_query(db, insert_query, params, fetch=False)
    except Exception as e:
        print(f"Errore durante l'inserimento risposta: {e}")
        raise HTTPException(status_code=500, detail="Errore interno durante l'inserimento della risposta")
    
    if not answer_id:
        raise HTTPException(status_code=500, detail="Errore interno durante l'inserimento della risposta")

    # Aggiunta task in background per valutazione
    background_tasks.add_task(
        evaluate_validity,
        answer=data.answer,
        question=question_check['question'],
        answer_id=answer_id,
        db=db
    )
    background_tasks.add_task(
        evaluate_coherence_qa,
        answer=data.answer,
        question=question_check['question'],
        answer_id=answer_id,
        db=db
    )

    return Response(status_code=201)

@router.get("/{answer_id}/validations")
def get_validations_to_answer(answer_id: int, db: Annotated[mariadb.Connection, Depends(db_connection)])->List[Rating]:
    """
    Retrieve ratings by its answer_ID.
    """
    select_query = """
        SELECT r.id, r.answer_id, r.question_id, u.username, r.rating, r.flag_ia 
        FROM ratings r JOIN users u ON r.user_id = u.id
        WHERE answer_id = ?
    """
    params = (answer_id,)
    rows = execute_query(db, select_query, params, dict=True)
    if not rows:
        raise HTTPException(status_code=404, detail="No answers found for the question")
    return [Rating(**row) for row in rows]