from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_signup_and_login_flow():
    # signup
    email = "testuser@example.com"
    client.post("/api/auth/signup", json={
        "name": "Test User",
        "email": email,
        "password": "Password123!",
        "role": "student",
    })
    # login
    r = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token


def test_list_quizzes_public():
    r = client.get("/api/quizzes")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


