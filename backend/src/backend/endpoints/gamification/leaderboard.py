from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
import mariadb
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user
from endpoints.gamification.models import User
from endpoints.auth.auth import get_current_user_id

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/")
def get_leaderboard(db: Annotated[mariadb.Connection, Depends(db_connection)])->List[User]:
    
    select_query = """
    SELECT u.username, l.score
    FROM   users u JOIN leaderboard l ON u.id = l.user_id
    ORDER BY score DESC"""
    
    users = execute_query(db, select_query, dict = True)
    
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return [User(**user) for user in users]





@router.get("/user")
def get_user_position(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[str, Depends(get_current_user)],
) -> int:
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Errore: l'utente deve autenticarsi per ottenere la propria posizione in classifica",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = current_user
    user_id = get_current_user_id(username, db)

    select_query = """
        SELECT 
            (SELECT COUNT(*) + 1
            FROM leaderboard l2 
            JOIN users u2 ON l2.user_id = u2.id
            WHERE l2.score > l.score 
                OR (l2.score = l.score AND u2.id < u.id)
            ) AS position
        FROM leaderboard l
        JOIN users u ON l.user_id = u.id
        WHERE l.user_id = ?
    """

    user = execute_query(db, select_query, (user_id,), fetchone=True, dict=True)

    if not user or "position" not in user:
        raise HTTPException(status_code=404, detail="Posizione dell'utente non trovata")

    return user["position"]

