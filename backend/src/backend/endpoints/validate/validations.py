from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Literal, Optional
import mariadb
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user, get_current_user_id
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
            detail="Errore: l'utente deve essere loggato per poter fare valutazioni",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = current_user if type == "human" else None

    user_id = get_current_user_id(username, db)

    insert_query = """
        INSERT INTO ratings (answer_id, question_id, user_id, rating, flag_ia)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (data.answer_id, data.question_id, user_id,data.rating, data.flag_ia)
    
    execute_query(db, insert_query, params, fetch=False)

    return Response(status_code=201)



