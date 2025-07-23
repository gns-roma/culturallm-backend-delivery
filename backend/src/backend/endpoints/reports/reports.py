from typing import Annotated, Literal, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
import mariadb
from endpoints.reports.models import Report
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user, get_current_user_id


router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/")
def submit_report(
    data: Report,
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[Optional[str], Depends(get_current_user)] = None) -> Response:

    if current_user is None:
        return Response(status_code=401, content="Errore: l'utente deve essere loggato per inviare un report")
    
    ##Si cancellerà perché la gestiremo nel frontend
    if data.question_id is None and data.answer_id is None:
        raise HTTPException(status_code=400, detail="Devi specificare question_id o answer_id")

    user_id = get_current_user_id(current_user, db)

    insert_query = "INSERT INTO reports (user_id, reason, question_id, answer_id) VALUES (?, ?, ?, ?)"

    params = (user_id, data.report, data.question_id, data.answer_id)

    execute_query(db, insert_query, params, fetch=False)

    return Response(status_code=201)