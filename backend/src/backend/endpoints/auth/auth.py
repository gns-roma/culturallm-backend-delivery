from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import mariadb
import logging
from exceptions import handle_exceptions, Error
from crypto.jwt import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from crypto.models import TokenExpired, TokenInvalid, TokenMissing
from db.mariadb import db_connection, execute_query
from endpoints.auth.models import RefreshTokenRequest, SignupRequest, Token
from crypto.password import get_salt, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token : Annotated[str, Depends(oauth2_scheme)]) -> str:
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise TokenInvalid("Token non valido")
    except (TokenExpired, TokenInvalid, TokenMissing) as token_exception:
        raise HTTPException(
            status_code=401,
            detail=str(token_exception),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username



def get_current_user_id(
        username: str, 
        conn: mariadb.Connection
) -> int | None:
    
    if not username: return None

    select_query = """
        SELECT id FROM users WHERE username = ?
    """

    user_id = execute_query(conn, select_query, (username,), fetchone=True)
    
    if user_id: return user_id[0]
    else: return None




@router.post("/login", responses={
    401: {
        "model": Error,
        "description": "Email o password errati",
    },
    422: {
        "model": Error,
        "description": "Errore di validazione dei dati di input"
    }
})
@handle_exceptions()
def login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    conn: mariadb.Connection = Depends(db_connection)
) -> Token:
    #Recover password_hash and salt
    auth_query = "SELECT password_hash, salt FROM users WHERE username = ?"
    result = execute_query(conn, auth_query, (data.username,))
    
    if not result:
        logger.info(f"result è vuoto: {result}")
        raise HTTPException(status_code=401, detail="Email o password errati")

    stored_hash, stored_salt_hex = result[0] 
    stored_salt = bytes.fromhex(stored_salt_hex)

    #Verify password
    if not verify_password(stored_hash, stored_salt, data.password):
        logger.info(f"Email o password errati: \nstored_hash:{stored_hash}, \nstored_salt:{stored_salt}, \npassword: {data.password}")
        raise HTTPException(status_code=401, detail="Email o password errati")
    
    #Aggiorna last_login
    update_query = """
        UPDATE users 
        SET last_login = NOW()
        WHERE username = ?
    """
    execute_query(conn, update_query, (data.username,), fetch=False)

    return Token(
        access_token=create_access_token({"sub": data.username}), 
        refresh_token=create_refresh_token({"sub": data.username}),
        token_type="bearer"
    )




@router.post("/signup", responses={
    400: {
        "model": Error,
        "description": "Username o email già registrati",
    },
    422: {
        "model": Error,
        "description": "Errore di validazione dei dati di input",
    }
})
@handle_exceptions()
def signup(data: SignupRequest, conn: Annotated[mariadb.Connection, Depends(db_connection)]) -> Token:
    # Controlla se utente o email esistono già
    check_query = """
        SELECT username 
        FROM users 
        WHERE username = ? OR email = ?
    """
    existing = execute_query(conn, check_query, (data.username, data.email))
    if existing:
        logger.info(f"Username o email già registrati: \nemail:{data.email} \nusername:{data.username}")
        raise HTTPException(status_code=400, detail="Username o email già registrati")
    
    # prendo i salt per la passwrod
    salt_pwd = get_salt(16)
    salt_hex = salt_pwd.hex()
    pwd_hash = hash_password(data.password, salt_pwd)
    
    insert_query = """
        INSERT INTO users (username, email, nation, password_hash, salt, signup_date, last_login)
        VALUES (?, ?, ?, ?, ?, NOW(), NOW())
    """

    execute_query(conn, insert_query, (data.username, data.email, data.nation, pwd_hash, salt_hex), fetch=False)

    return Token(
        access_token=create_access_token({"sub": data.username}), 
        refresh_token=create_refresh_token({"sub": data.username}),
        token_type="bearer"
    )


@router.post("/refresh", responses={
    422: {
        "model": Error,
        "description": "Errore di validazione dei dati di input",
    },
    401: {
        "model": Error,
        "description": "Token non valido",
    },
})
@handle_exceptions()
def refresh_token(request: RefreshTokenRequest):
    
    if not request.refresh_token:
        logger.info("Refresh token non fornito")
        raise HTTPException(status_code=422, detail="Refresh token non fornito")

    payload = decode_refresh_token(request.refresh_token)
    username = payload.get("sub")
    
    if username is None:
        logger.info("Refresh token non valido")
        raise HTTPException(status_code=401, detail="Token non valido")

    return Token(
        access_token=create_access_token({"sub": username}),
        refresh_token=create_refresh_token({"sub": username}),
        token_type="bearer"
    )
