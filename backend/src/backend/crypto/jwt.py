import os
import jwt
from datetime import datetime, timedelta, timezone

from crypto.models import TokenExpired, TokenInvalid, TokenMissing

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

if not SECRET_KEY or not REFRESH_SECRET_KEY:
    raise RuntimeError("Environment variables JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY must be set.")

#encode data in a token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#create a refresh token
def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

#decode token and return a dict with data
def decode_access_token(token: str) -> dict:
    try:
        if not token:
            raise TokenMissing("Token non fornito")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpired("Token scaduto")
    except jwt.InvalidTokenError:
        raise TokenInvalid("Token non valido")

def decode_refresh_token(token: str) -> dict:
    try:
        if not token:
            raise TokenMissing("Token non fornito")
        
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpired("Token scaduto")
    except jwt.InvalidTokenError:
        raise TokenInvalid("Token non valido")