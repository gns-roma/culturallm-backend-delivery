from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ProfileSummary(BaseModel):
    username: str
    email: EmailStr
    signup_date: datetime
    last_login: datetime
    nation: str | None = None
    level: int
    level_threshold: int
    num_questions: int
    num_answers: int
    score: int
    rank: int
    #profile_picture: str | None = None

class UpdateUserData(BaseModel):
    username: str | None = None
    password: str | None = None