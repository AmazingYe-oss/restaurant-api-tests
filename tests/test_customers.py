import requests
import os
from reservation_data import build_reservation_payload
from datetime import date,timedelta
from reservation_api import create_reservation
from uuid import uuid4


def test_customer_can_get_own_profile(login_data,base_url):
    token = login_data["accessToken"]
    customer_id = login_data["customerId"]

    response = requests.get(
        f"{base_url}/api/customers/{customer_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    data = response.json()

    assert response.status_code==200
    assert data['id']==customer_id
    assert data['email']==login_data['email']


def test_get_customer_without_token_returns_401(base_url):
    response = requests.get(
        f"{base_url}/api/customers/2",
        timeout=10,
    )
    assert response.status_code==401
    assert response.json()['path']=='/api/customers/2'
    assert 'Authentication required' in response.json()['message']



def test_customer_cannot_get_another_profile(base_url, login_data,register_user):
    customer_id=login_data['customerId']
    customer_new_id=register_user['customerId']
    assert register_user["role"] == "CUSTOMER"
    assert customer_new_id != customer_id
    access_new_token=register_user['accessToken']
    response = requests.get(
            f"{base_url}/api/customers/{customer_id}",
            headers={"Authorization": f"Bearer {access_new_token}"},
            timeout=10,
        )


    assert response.status_code==403
    assert response.json()['path']==f"/api/customers/{customer_id}"


def test_get_customer_with_invalid_token_returns_401(base_url):
    response = requests.get(
        f"{base_url}/api/customers/2",
        headers={"Authorization": "Bearer invalid-token"},
        timeout=10,
    )

    # 请补充状态码和响应路径断言

    assert response.status_code==401
    assert response.json()['path']=='/api/customers/2'
