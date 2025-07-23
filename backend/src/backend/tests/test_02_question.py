from fastapi.testclient import TestClient
import pytest
from typing import List
from endpoints.answers.models import AnswerValues
from endpoints.validate.models import RatingValues
from endpoints.questions.models import QuestionValues

from backend import app

#RISCRIVERLI TUTTI MEGLIO
client = TestClient(app)
access_tokens = [] 
headers = []
answer_ids = []

@pytest.mark.order(4)
def test_login():
    response = client.post("/auth/login/", data={"username": "sorcarlo", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "Mariano", "email": "marianogiusti@libero.it", "password": "luit1perdon4!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})


@pytest.mark.order(5)
def test_submit_question():
    payload = {"question": "Chi ha dipinto la cappella sistina?", "topic": "🎨 Arte"}
    response = client.post("/questions/", params={"type":"human"}, json=payload, headers=headers[0])
    assert response.status_code == 201
    response = client.post("/questions/", params={"type": "human"}, json = payload)
    assert response.status_code == 401

@pytest.mark.order(6)
def test_answer_to_question():
    ##Risposta di un utente
    response = client.get("/questions/random/to_answer", headers=headers[1])
    assert response.status_code == 200
    question_id = response.json()["id"]
    payload = {"answer":"Caravaggio ha dipinto la Cappella Sistina", "question_id":question_id}
    response = client.post("/answers/", params={"type": "human"}, json = payload, headers=headers[1])
    assert response.status_code == 201


    ##Risposta dell'altro
    response = client.get("/questions/random/to_answer", headers=headers[0])
    assert response.status_code == 200
    question_id = response.json()["id"]
    payload = {"answer":"Michelangelo Buonarroti ha dipinto la Cappella Sistina", "question_id":question_id}
    response = client.post("/answers/", params={"type": "human"}, json = payload, headers=headers[0])
    assert response.status_code == 201

@pytest.mark.order(7)
def test_get_answers_and_validate():


    ##Gli apparirà da valutare la risposta dell'llm oppure dell'altro utente
    random_question = client.get("/questions/qa_to_validate", headers=headers[0])
    assert random_question.status_code == 200
    question_id = random_question.json()["question_id"]
    answer_id = random_question.json()["answer_id"]

    payload = {"rating":5, "answer_id":answer_id, "question_id":question_id, "flag_ia":True}
    rating_response = client.post("/validation/rating", json=payload, headers=headers[0])
    assert rating_response.status_code == 201


    random_question = client.get("/questions/qa_to_validate", headers=headers[0])
    assert random_question.status_code == 200
    question_id = random_question.json()["question_id"]
    answer_id = random_question.json()["answer_id"]

    payload = {"rating":1, "answer_id":answer_id, "question_id":question_id, "flag_ia":False}
    rating_response = client.post("/validation/rating", json=payload, headers=headers[0])
    assert rating_response.status_code == 201



