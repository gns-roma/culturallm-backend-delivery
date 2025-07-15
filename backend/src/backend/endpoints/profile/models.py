from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr
    date: datetime
    nation: str
    #profile_picture: str | None = None

class UpdateUserData(BaseModel):
    username: str | None = None
    password: str | None = None