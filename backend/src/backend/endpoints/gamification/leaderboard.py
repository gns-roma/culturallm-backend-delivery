from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
import mariadb
from db.mariadb import db_connection, execute_query
from endpoints.auth.auth import get_current_user
from endpoints.gamification.models import User

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("/best")
def get_best_leaderboard(db: Annotated[mariadb.Connection, Depends(db_connection)])-> List[User]:
    select_query = """
    SELECT u.username, l.score 
    FROM leaderboard l JOIN users u ON l.user_id = u.id 
    ORDER BY score DESC LIMIT 10"""
    users = execute_query(db, select_query, dict = True)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return [User(**user) for user in users]



@router.get("/")
def get_leaderboard(db: Annotated[mariadb.Connection, Depends(db_connection)])->List[User]:
    select_query = """
    SELECT u.username, COALESCE(l.score, 0) AS score
    FROM   users u LEFT JOIN leaderboard AS l ON u.id = l.user_id
    ORDER BY score DESC"""
    users = execute_query(db, select_query, dict = True)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return [User(**user) for user in users]



@router.get("/user")
def get_user_position(
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    current_user: Annotated[User, Depends(get_current_user)],
)->User:
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: User must be logged in to get their position.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = current_user
    select_query = """
    SELECT u.username, l.score,
        (SELECT COUNT(*) + 1
         FROM leaderboard
         WHERE score > l.score) AS position
    FROM leaderboard l JOIN users u ON l.user_id = u.id
    WHERE u.username = ?
    UNION ALL
    SELECT username, 0, NULL
    FROM users
    WHERE username = ? AND username NOT IN (SELECT username FROM leaderboard JOIN users ON leaderboard.user_id = users.id)
    """
    user = execute_query(db, select_query, (username, username),fetchone=True, dict=True)
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    return User(**user)
