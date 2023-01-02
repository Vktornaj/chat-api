from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_pipeline():
    response = client.post(
        "/users/register",
        headers={'Content-Type': 'application/json'},
        json={
            "first_name":"Victor Eduardo",
            "last_name":"Garcia Najera",
            "email":"victor2211812@gmail.com",
            "password":"Secret12345"
        }
    )
    assert response.status_code == 201

    response = client.post(
        "/users/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"username": "victor2211812@gmail.com", "password": "Secret12345"}
    )
    response_json = response.json()
    assert response.status_code == 200

    response = client.delete(
        "/users/me",
        headers = {
            'Authorization': f'{response_json["token_type"]} {response_json["access_token"]}',
            'Content-Type': 'application/json'
        },
        json={
            "password": "Secret12345"
        }
    )
    assert response.status_code == 200
