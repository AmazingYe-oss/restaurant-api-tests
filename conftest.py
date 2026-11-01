from pathlib import Path

from dotenv import load_dotenv

# Load the project configuration before collecting tests.
load_dotenv(Path(__file__).resolve().parent / ".env")
import os
import pytest
import requests

@pytest.fixture
def login_data(base_url):
    # 把现有测试里的登录请求放到这里
    # 密码继续从 os.environ["TEST_LOGIN_PASSWORD"] 读取
    # 检查登录状态码为 200
    # 最后返回


    login_response = requests.post(
                f"{base_url}/api/auth/login",
                json={
                    "email": "user@example.com",
                    "password": os.environ["TEST_LOGIN_PASSWORD"]
                },
                timeout=10,
            )

    assert login_response.status_code==200,login_response.text
    return login_response.json()


@pytest.fixture
def base_url():
    return os.getenv(
        "TEST_BASE_URL",
        "http://127.0.0.1:18080",
    ).rstrip("/")


@pytest.fixture
def reservation_ids(base_url, login_data):
    ids = []
    headers = {
        "Authorization": f"Bearer {login_data['accessToken']}"
    }

    yield ids

    for reservation_id in ids:
        url = f"{base_url}/api/reservations/{reservation_id}"
        response=requests.get(url=url,timeout=10,headers=headers)
        assert response.status_code==200
        if response.json()['status'] in ('PENDING','CONFIRMED'):
            response_delete=requests.delete(url=url, timeout=10, headers=headers)
            assert response_delete.status_code==204
