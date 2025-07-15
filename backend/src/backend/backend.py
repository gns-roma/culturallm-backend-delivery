import logging
import os
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError

from db.pool import init_pool
from endpoints.questions import topics, questions
from endpoints.profile import profile
from endpoints.auth import auth
from endpoints.answers import answers
from endpoints.validate import validations
from endpoints.gamification import leaderboard
from exceptions import request_validation_exception_handler


db_host = os.getenv("DB_HOST", "culturallm-db")
db_port = int(os.getenv("DB_PORT", 3306))
db_user = os.getenv("DB_USER", "user")
db_password = os.getenv("DB_PASSWORD", "userpassword")
db_name = os.getenv("DB_NAME", "culturallm_db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    yield


app = FastAPI(lifespan=lifespan)

app.title = "Backend CulturaLLM API"
app.description = "API for managing CulturaLLM project."

app.exception_handler(RequestValidationError)(request_validation_exception_handler)

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.INFO)
# se vogliamo attivare i log di debug possiamo settare il livello a logging.DEBUG
# logger.setLevel(logging.DEBUG)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(topics.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(validations.router)
app.include_router(leaderboard.router)