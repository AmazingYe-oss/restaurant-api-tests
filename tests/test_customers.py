import requests
import os


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
