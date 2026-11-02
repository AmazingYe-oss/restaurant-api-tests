from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
import os
import pytest
import requests
from uuid import uuid4
from datetime import date, timedelta
import random

def gen_phone():
    prefixes = ['133', '149', '153', '173', '177', '180', '181', '189', '150', '151', '152', '155', '156', '157', '158', '159', '130', '131', '132', '135', '136', '137', '138', '139', '186', '187', '188', '185', '176', '178']
    return random.choice(prefixes) + ''.join(random.choices('0123456789', k=8))

@pytest.fixture
def register_user(base_url):
    payload = {'fullName': f'test_{uuid4().hex[:5]}_user', 'email': f'{uuid4().hex}@example.com', 'password': os.environ['TEST_LOGIN_PASSWORD'], 'phone': gen_phone()}
    register_response = requests.post(f'{base_url}/api/auth/register', json=payload)
    assert register_response.status_code == 201
    register_response_json = register_response.json()
    assert register_response_json['fullName'] == payload['fullName']
    assert register_response_json['email'] == payload['email']
    assert isinstance(register_response_json['accessToken'], str)
    assert register_response_json['accessToken'] != ''
    return register_response_json

@pytest.fixture
def login_user(base_url):

    def login(email='user@example.com'):
        response = requests.post(f'{base_url}/api/auth/login', json={'email': email, 'password': os.environ['TEST_LOGIN_PASSWORD']}, timeout=10)
        assert response.status_code == 200, response.text
        return response.json()
    return login

@pytest.fixture
def base_url():
    return os.getenv('TEST_BASE_URL', 'http://127.0.0.1:18080').rstrip('/')

@pytest.fixture
def reservation_ids(base_url, login_data):
    ids = []
    headers = {'Authorization': f'Bearer {login_data['accessToken']}'}
    yield ids
    for reservation_id in ids:
        url = f'{base_url}/api/reservations/{reservation_id}'
        response = requests.get(url=url, timeout=10, headers=headers)
        assert response.status_code == 200
        if response.json()['status'] in ('PENDING', 'CONFIRMED'):
            response_delete = requests.delete(url=url, timeout=10, headers=headers)
            assert response_delete.status_code == 204

@pytest.fixture
def login_data(login_user):
    return login_user()
