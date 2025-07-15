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

    response = client.post("/auth/login/", data={"username": "tamburini", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "magatrump", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "salvobuzzi", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "cruciani", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "tony777", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "sidebaby", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "wanna", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

    response = client.post("/auth/login/", data={"username": "montalbano", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    access_tokens.append(response.json()["access_token"])
    headers.append({"Authorization": f"Bearer {response.json()['access_token']}"})

@pytest.mark.order(5)
def test_submit_question():
    for header in headers:
        payload = {"question": "Chi ha dipinto la capella Sistina", "topic": "arte"}
        response = client.post("/questions/", params={"type":"human"}, json=payload, headers=header)
        assert response.status_code == 201
        response = client.post("/questions/", params={"type": "human"}, json = payload)
        assert response.status_code == 401

@pytest.mark.order(6)
def test_answer_to_question():
    for i,header in enumerate(headers):
        for j in range(8):
            response = client.get("/questions/random/to_answer", headers=header)
            assert response.status_code == 200
            question_id = response.json()["id"]
            payload = {"answer":f"{j+1}° Risposta generica dell'{i+1}° utente a una domanda generica di cultura generale.", "question_id":question_id}
            response = client.post("/answers/", params={"type": "human"}, json = payload, headers=header)
            assert response.status_code == 201

@pytest.mark.order(7)
def test_get_answers_and_validate():
    #Per ogni utente, prendi una domanda casuale e recupera le risposte
    for header in headers:
        random_question = client.get("/questions/random", headers=header)
        assert random_question.status_code == 200
        question_id = random_question.json()["id"]
        response = client.get(f"/questions/{question_id}/answers", headers=header)
        assert response.status_code == 200
        #Dopo aver ottenuto la lista di risposte, ogni utente a turno le valida
        if response.status_code == 200:
            answers = response.json()
            assert isinstance(answers, List)

            if answers:
                for answer in answers:
                    answer_id = answer["id"]
                    answer_ids.append(answer_id)
                    payload = {"rating":5, "answer_id":answer_id, "question_id":question_id, "flag_ia":False}
                    rating_response = client.post("/validation/rating", json=payload, headers=header)
                    assert rating_response.status_code == 201
    
@pytest.mark.order(8)
def test_get_validations():
    for answer_id in answer_ids:      
        validations_response = client.get(f"/answers/{answer_id}/validations")
        assert validations_response.status_code == 200
        if validations_response.status_code == 200:
            validations = validations_response.json()
            assert isinstance(validations, List)
        


@pytest.mark.order(9)
def test_get_answer_to_question():
    for header in headers:
        response = client.get("/questions/qa_to_validate", headers=header)
        assert response.status_code == 200
