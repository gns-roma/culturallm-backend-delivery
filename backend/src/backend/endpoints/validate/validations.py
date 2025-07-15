from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Literal, Optional
import mariadb
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user
from endpoints.validate.models import RatingValues

router = APIRouter(prefix="/validation", tags=["validation"])

@router.post("/rating")
def rate_answers(
    data: RatingValues,
    db: mariadb.Connection = Depends(db_connection),
    current_user: Optional[str] = Depends(get_current_user),
    type: Literal["human", "llm"] = "human"
) -> Response:

    if type == "human" and current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in to answer a question.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = current_user if type == "human" else None

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
        INSERT INTO ratings (answer_id, question_id, user_id, rating, flag_ia)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (data.answer_id, data.question_id, user_id,data.rating, data.flag_ia)
    try:
        execute_query(db, insert_query, params, fetch=False)
    except mariadb.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Error inserting rating")   
    return Response(status_code=201)



