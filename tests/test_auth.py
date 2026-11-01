import requests
import os
from uuid import uuid4
import pytest

def test_login_with_wrong_password_returns_401(base_url):
    payload={"email":'user@example.com','password':'12345687'}
    response=requests.post(
         f"{base_url}/api/auth/login",
        json=payload,
        timeout=10,
    )
    assert response.status_code ==401
    assert response.json()['path']=='/api/auth/login'
    assert response.json()["message"] == "Invalid email or password"

@pytest.mark.parametrize(
        "payload",
        [
             {"email": "user@example.com"},
        {"email": "user@example.com", "password": ""},
        {"email": "user@example.com", "password": "   "},
        ],
        ids=['missing-password','empty-password','blank-password']
)
def test_login_without_password_returns_400(base_url,payload):
    response=requests.post(
        f"{base_url}/api/auth/login",
        json=payload,
        timeout=10
    )
    assert response.status_code==400
    assert response.json()['path']=='/api/auth/login'
    assert "password is required" in response.json()["message"]


def test_login_with_valid_credentials_returns_token(base_url):
    payload = {
    "email": "user@example.com",
    "password": os.environ["TEST_LOGIN_PASSWORD"],
}
    response=requests.post(
            f"{base_url}/api/auth/login",
            json=payload,
            timeout=10
        )
    assert response.status_code==200
    assert response.json()['email']=='user@example.com'
    assert isinstance(response.json()['accessToken'],str)
    assert response.json()['accessToken'] !=''


def test_register_customer_returns_201(base_url):
    payload = {
        "fullName": "Automation Customer",
        "email": f"test_{uuid4().hex}@example.com",
        "password": os.environ["TEST_LOGIN_PASSWORD"],
    }

    response = requests.post(
        f"{base_url}/api/auth/register",
        json=payload,
        timeout=10,
    )

    assert response.status_code==201
    response_json=response.json()
    assert isinstance(response_json['accessToken'],str)
    assert response_json['accessToken'] !=''
    assert response_json["email"] == payload["email"]
    assert response_json["fullName"] == payload["fullName"]
    assert response_json["role"] == "CUSTOMER"
    assert isinstance(response_json["customerId"], int)
    assert response_json["customerId"] > 0
