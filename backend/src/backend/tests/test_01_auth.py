import os
from fastapi.testclient import TestClient
from backend import app

import pytest
from db.pool import init_pool

client = TestClient(app)
access_token = None

@pytest.fixture(scope="session", autouse=True)
def initialize_db_pool():
    db_host = os.getenv("DB_HOST", "culturallm-db")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER", "user")
    db_password = os.getenv("DB_PASSWORD", "userpassword")
    db_name = os.getenv("DB_NAME", "culturallm_db")

    init_pool(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

@pytest.mark.order(1)
def test_signup():
    response = client.post("/auth/signup/", json={"username": "sorcarlo", "email": "carlo.verdone1927@gmail.com", "nation":"Italia","password": "forzamaggica"})
    assert response.status_code == 422
    response = client.post("/auth/signup/", json={"username": "sorcarlo", "email": "carlo.verdone1927@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "Mariano", "email": "marianogiusti@libero.it", "nation":"Italia","password": "luit1perdon4!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "Mariano", "email": "marianogiusti@libero.it", "nation":"Italia","password": "luit1perdon4!"})
    assert response.status_code == 400
    response = client.post("/auth/signup/", json={"username": "hahah", "email": "noemail", "nation":"Italia","password": "prova"})
    assert response.status_code == 422
    response = client.post("/auth/signup/", json={"username": "hahah", "email": "noemail@silos", "nation":"Italia","password": "prova"})
    assert response.status_code == 422
    response = client.post("/auth/signup/", json={"username": "tamburini", "email": "tamburini.direttore@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "magatrump", "email": "thedonald@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "salvobuzzi", "email": "buzzi.salvatore@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "cruciani", "email": "cruciani@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "tony777", "email": "tonyeffe@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "sidebaby", "email": "darkside@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "wanna", "email": "wannamarchi@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "montalbano", "email": "mantalbano@gmail.com", "nation":"Italia","password": "forzamaggica1927!"})
    assert response.status_code == 200
    response = client.post("/auth/signup/", json={"username": "montalbano2", "email": "mantalbano2@gmail.com", "nation":"Italia","password": "forzamaggica192711111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111!"})
    assert response.status_code == 422


    
@pytest.mark.order(2)
def test_login():
    response = client.post("/auth/login/", data={"username": "sorcarlo", "password": "forzamaggica1927!"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    global access_token
    access_token = response.json()["access_token"]

@pytest.mark.order(3)
def test_profile():
    headers = {"Authorization": f"Bearer {access_token}"}
    print(headers)
    response = client.get("/profile/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "username": "sorcarlo", 
        "email": "carlo.verdone1927@gmail.com", 
        "signup_date": response.json()["signup_date"], 
        "last_login": response.json()["last_login"],
        "nation": "Italia"
    }
