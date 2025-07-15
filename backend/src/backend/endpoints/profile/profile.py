import hashlib
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
import mariadb
import pydenticon
from exceptions import Error
from endpoints.profile.models import UpdateUserData
from endpoints.auth.auth import get_current_user
from db.mariadb import db_connection, execute_query
from endpoints.questions.models import Question
from endpoints.answers.models import Answer
from endpoints.profile.models import ProfileSummary
from endpoints.gamification.models import User
from endpoints.gamification.leaderboard import get_user_position
from endpoints.profile.levels import get_level_and_threshold    



router = APIRouter(prefix="/profile", tags=["profile"])

generator = pydenticon.Generator(
        5, 5,
        digest=hashlib.sha1,
        foreground = [ "rgb(128,36,51)" ],
        background="rgb(255,255,255)",
    )


@router.get("/")
def profile(
    current_user: Annotated[str, Depends(get_current_user)], 
    db: Annotated[mariadb.Connection, Depends(db_connection)]
) -> ProfileSummary:
 
    get_query = """
        SELECT u.username, u.email, u.signup_date, u.last_login, u.nation,COUNT(q.id) AS num_questions,COUNT(a.id) AS num_answers
        FROM users u LEFT JOIN questions q ON q.user_id = u.id LEFT JOIN answers a ON a.user_id = u.id
        WHERE u.username = ?
        GROUP BY u.id;
    """
    try:
        result = execute_query(db, get_query, (current_user,), dict=True, fetchone=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore DB: {e}")
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_rank : User = get_user_position(db, current_user)
    if not user_rank:
        raise HTTPException(status_code=404, detail="User data not found")
    result["rank"] = user_rank.position 
    result["score"]= user_rank.score 
    result["level"] = get_level_and_threshold(user_rank.score)["level"]
    result["level_threshold"] = get_level_and_threshold(user_rank.score)["next_threshold"]

    return ProfileSummary(**result)



@router.put("/edit/")
def edit_profile(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[mariadb.Connection, Depends(db_connection)],
    data : UpdateUserData
) -> Response:
    """
    Edit the profile of the current user.
    """
    if not data.username and not data.password:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields = []
    params = []

    if data.username:
        update_fields.append("username = ?")
        params.append(data.username)
    
    if data.password:
        from crypto.password import get_salt, hash_password
        salt_pwd = get_salt(16)
        salt_hex = salt_pwd.hex()
        pwd_hash = hash_password(data.password, salt_pwd)

        update_fields.append("password_hash = ?, salt = ?")
        params.extend([pwd_hash, salt_hex])

    params.append(current_user)
    
    update_query = f"""
        UPDATE users 
        SET {', '.join(update_fields)}
        WHERE user = ?
        """
    
    execute_query(db, update_query, tuple(params), fetch=False)
    
    return Response(status_code=204)  # No Content, successful update without returning data



@router.get("/avatar/", response_class=Response, responses={
    200: {
        "content": {
            "image/png": {
                "example": "base64_encoded_image_data"
            }
        },
    },
    422: {
        "model": Error
    }
})
def get_avatar(username: str = Query(...)) -> Response:
    """
    Retrieve the avatar of the user.
    """
    image = generator.generate(
        data = username, 
        width = 200, 
        height = 200, 
        padding = (20, 20, 20, 20),
        output_format='png'
    )

    return Response(content=image, media_type="image/png")




"""Function to retrieve all questions submitted by the user."""
@router.get("/questions")
def get_user_questions(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[mariadb.Connection, Depends(db_connection)])-> List[Question]:

    if current_user is None:
        return Response(status_code=401, content="Unauthorized: User must be logged in to submit a human question.")

    username = current_user

    get_query = """
        SELECT q.id, q.type, u.username, q.question, q.topic, q.cultural_specificity, q.cultural_specificity_notes
        FROM questions q JOIN users u ON q.user_id = u.id
        WHERE u.username = ?
        ORDER BY q.id ASC
    """
    try:
        rows = execute_query(db, get_query, (username,), dict=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore DB: {e}")
    
    if rows is None:
        raise HTTPException(status_code=404, detail="Nessuna domanda trovata per l'utente.")
    
    return [Question(**row) for row in rows]


@router.get("/answers")
def get_user_answers(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[mariadb.Connection, Depends(db_connection)])-> List[Answer]:

    if current_user is None:
        return Response(status_code=401, content="Unauthorized: User must be logged in to submit a human question.")

    username = current_user

    get_query = """
        SELECT a.id, a.type, u.username, a.question_id, a.answer
        FROM answers a JOIN users u ON a.user_id = u.id
        WHERE u.username = ?
        ORDER BY a.id ASC
    """
    try:
        rows = execute_query(db, get_query, (username,), dict=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore DB: {e}")
    
    if rows is None:
        raise HTTPException(status_code=404, detail="Nessuna risposta trovata per l'utente.")
    
    return [Answer(**row) for row in rows]



