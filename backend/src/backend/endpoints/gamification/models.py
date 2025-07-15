from typing import Literal
from pydantic import BaseModel


class User(BaseModel):
    username: str | None
    score: int
    position: int | None = None