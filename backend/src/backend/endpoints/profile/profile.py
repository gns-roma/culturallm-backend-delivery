import hashlib
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
import mariadb
import pydenticon
from exceptions import Error
from endpoints.profile.models import UpdateUserData
from endpoints.auth.auth import get_current_user
from db.mariadb import db_connection, execute_query
from endpoints.questions.models import QuestionBasic
from endpoints.auth.auth import get_current_user_id
from endpoints.answers.models import AnswerBasic
from endpoints.profile.models import ProfileSummary
from endpoints.gamification.leaderboard import get_user_position
from endpoints.profile.levels import get_level_and_threshold    
import re
import logging

router = APIRouter(prefix="/profile", tags=["profile"])
logger = logging.getLogger("app"
                           )
generator = pydenticon.Generator(
        5, 5,
        digest=hashlib.sha1,
        foreground = [ "rgb(128,36,51)" ],
        background="rgb(255,255,255)",
    )



## Questo endpoint ritorna tutte le informazioni necessarie per il profilo dell'utente
@router.get("/")
def profile(
    current_user: Annotated[str, Depends(get_current_user)], 
    db: Annotated[mariadb.Connection, Depends(db_connection)]
) -> ProfileSummary:
    logger.info(f"Looking up user: {current_user}")
    get_query = """
        SELECT u.username, u.email, u.signup_date, u.last_login, u.nation, l.num_questions, l.num_answers, l.score
        FROM users u JOIN leaderboard l ON u.id = l.user_id
        WHERE u.username = ?
    """
    result = execute_query(db, get_query, (current_user,), dict=True, fetchone=True)
    if not result:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    result["level"] = get_level_and_threshold(result["score"])["level"]
    result["level_threshold"] = get_level_and_threshold(result["score"])["next_threshold"]
    
    user_rank : int = get_user_position(db, current_user)

    if not user_rank:
        raise HTTPException(status_code=404, detail="User position not found")
    result["rank"] = user_rank

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
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

    if data.username:
        # Verifica se username esiste già
        existing_user = execute_query(
            db, "SELECT 1 FROM users WHERE username = ?", (data.username,), fetch=True
        )
        if existing_user:
            raise HTTPException(status_code=409, detail="Username già esistente")
    
    if data.password and not validate_password(data.password):
        raise HTTPException(status_code=400, detail="Password non valida o troppo debole")

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
        WHERE username = ?
        """
    
    execute_query(db, update_query, tuple(params), fetch=False)
    
    return Response(status_code=204)


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





##Questo endpoint ritorna le domande scritte dall'utente
@router.get("/questions/")
def get_user_questions(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[mariadb.Connection, Depends(db_connection)]) -> List[QuestionBasic]:

    if current_user is None:
        return Response(status_code=401, content="Errore: l'utente deve essere autenticato per ottenere tutte le domande che ha scritto")

    username = current_user

    user_id = get_current_user_id(username, db)

    get_query = """
        SELECT q.id, q.question, q.topic
        FROM questions q
        WHERE q.user_id = ?
        ORDER BY q.id ASC
    """
    rows = execute_query(db, get_query, (user_id,), dict=True)
    
    if rows is None:
        raise HTTPException(status_code=404, detail="Nessuna domanda scritta dall'utente.")
    
    return [QuestionBasic(**row) for row in rows]




##Questo endpoint ritorna le risposte scritte dall'utente
@router.get("/answers/")
def get_user_answers(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[mariadb.Connection, Depends(db_connection)])-> List[AnswerBasic]:

    if current_user is None:
        return Response(status_code=401, content="Unauthorized: User must be logged in to submit a human question.")

    username = current_user

    user_id = get_current_user_id(username, db)

    get_query = """
        SELECT a.id, q.topic, q.question, a.answer, l.score
        FROM answers a JOIN questions q ON a.question_id = q.id 
        JOIN logs l ON (l.action_id = a.id AND l.action_type="answer")
        WHERE a.user_id = ?
        ORDER BY a.id ASC
    """
    rows = execute_query(db, get_query, (user_id,), dict=True)
    
    if rows is None:
        raise HTTPException(status_code=404, detail="Nessuna risposta trovata per l'utente.")
    
    return [AnswerBasic(**row) for row in rows]



def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La password è troppo corta")
    if len(password) > 64:
        raise HTTPException(status_code=400, detail="La password è troppo lunga")

    if not re.fullmatch(r'[A-Za-z0-9!@#$%&+=*\-?.]+', password):
        raise HTTPException(status_code=400, detail="La password contiene caratteri non ammessi")

    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=400, detail="La password deve contenere almeno un numero")

    if not any(c.isalpha() for c in password):
        raise HTTPException(status_code=400, detail="La password deve contenere almeno una lettera")

    return True



