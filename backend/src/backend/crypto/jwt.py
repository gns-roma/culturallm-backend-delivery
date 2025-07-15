import jwt
from datetime import datetime, timedelta, timezone

from crypto.models import TokenExpired, TokenInvalid, TokenMissing

SECRET_KEY = "ade80556c6e8ce1fa9c1b15a46e1c345d7423fde8c6c0c471a90d54cbe9eee5a"
REFRESH_SECRET_KEY = "e1afea2d3cf36ec7233b5e1114dc35ed179d5075fd47328f6ba8d8f07121a4d5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

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