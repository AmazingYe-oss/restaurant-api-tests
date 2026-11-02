import os
from datetime import date, timedelta
import requests
from uuid import uuid4
import pytest

@pytest.mark.parametrize("number_of_guests", [2, 4])
def test_create_reservation_returns_201(login_data, base_url, reservation_ids,number_of_guests):
    token = login_data['accessToken']
    customer_id = login_data['customerId']
    payload = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': number_of_guests}
    response = requests.post(f'{base_url}/api/reservations', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': uuid4().hex}, timeout=10, json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    reservation_id = data['id']
    reservation_ids.append(reservation_id)
    assert isinstance(data['id'], int)
    assert data['id'] > 0
    assert data['customerId'] == customer_id
    assert data['restaurantId'] == payload['restaurantId']
    assert data['tableId'] == payload['tableId']
    assert data['reservationDate'] == payload['reservationDate']
    assert data['reservationTime'] == payload['reservationTime']
    assert data['numberOfGuests'] == payload['numberOfGuests']
    assert data['status'] == 'PENDING'
    response_reservation = requests.get(f'{base_url}/api/reservations/{reservation_id}', headers={'Authorization': f'Bearer {token}'}, timeout=10)
    assert response_reservation.status_code == 200
    assert response_reservation.json()['status'] == 'PENDING'
    response_delete = requests.delete(f'{base_url}/api/reservations/{reservation_id}', headers={'Authorization': f'Bearer {token}'}, timeout=10)
    assert response_delete.status_code == 204
    response_get = requests.get(f'{base_url}/api/reservations/{reservation_id}', headers={'Authorization': f'Bearer {token}'}, timeout=10)
    assert response_get.status_code == 200
    assert response_get.json()['status'] == 'CANCELLED'

def test_reservation_exceeding_table_capacity_returns_400(
    base_url, login_data, reservation_ids
):
    token=login_data['accessToken']
    customer_id = login_data['customerId']
    payload = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': 5}
    response = requests.post(f'{base_url}/api/reservations', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': uuid4().hex}, timeout=10, json=payload)
    if response.status_code == 201:
        reservation_ids.append(response.json()["id"])
    assert response.status_code == 400, response.text
    data = response.json()
    assert data['message']=='Number of guests exceeds table capacity'


def test_duplicate_reservation_returns_409(
    base_url, login_data, reservation_ids
):
    token=login_data['accessToken']
    customer_id=login_data['customerId']
    payload_1 = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': 1}

    response = requests.post(f'{base_url}/api/reservations', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': uuid4().hex}, timeout=10, json=payload_1)
    assert response.status_code == 201, response.text
    data = response.json()
    reservation_id = data['id']
    reservation_ids.append(reservation_id)
    assert isinstance(data['id'], int)
    assert data['id'] > 0
    assert data['customerId'] == customer_id
    assert data['restaurantId'] == payload_1['restaurantId']
    assert data['tableId'] == payload_1['tableId']
    assert data['reservationDate'] == payload_1['reservationDate']
    assert data['reservationTime'] == payload_1['reservationTime']
    assert data['numberOfGuests'] == payload_1['numberOfGuests']
    assert data['status'] == 'PENDING'
    response_reservation = requests.get(f'{base_url}/api/reservations/{reservation_id}', headers={'Authorization': f'Bearer {token}'}, timeout=10)
    assert response_reservation.status_code == 200
    assert response_reservation.json()['status'] == 'PENDING'
    payload_2 = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': 1}
    response_2 = requests.post(f'{base_url}/api/reservations', headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': uuid4().hex}, timeout=10, json=payload_2)
    if response_2.status_code == 201:
        reservation_ids.append(response_2.json()["id"])
    assert response_2.status_code==409
    assert 'Table is already booked for this time' in response_2.json()['message']



def test_same_idempotency_key_returns_same_reservation(base_url, login_data, reservation_ids):
    key = uuid4().hex
    headers = {'Authorization': f'Bearer {login_data['accessToken']}', 'Idempotency-Key': key}
    customer_id = login_data['customerId']
    payload = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': 1}
    response = requests.post(f'{base_url}/api/reservations', headers=headers, timeout=10, json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    reservation_id = data['id']
    reservation_ids.append(reservation_id)
    assert isinstance(data['id'], int)
    assert data['id'] > 0
    assert data['customerId'] == customer_id
    assert data['restaurantId'] == payload['restaurantId']
    assert data['tableId'] == payload['tableId']
    assert data['reservationDate'] == payload['reservationDate']
    assert data['reservationTime'] == payload['reservationTime']
    assert data['numberOfGuests'] == payload['numberOfGuests']
    assert data['status'] == 'PENDING'
    response_reservation = requests.get(f'{base_url}/api/reservations/{reservation_id}', headers=headers, timeout=10)
    assert response_reservation.status_code == 200
    assert response_reservation.json()['status'] == 'PENDING'
    response_2 = requests.post(f'{base_url}/api/reservations', headers=headers, timeout=10, json=payload)
    assert response_2.status_code == 201, response_2.text
    data_2 = response_2.json()
    reservation_id = data_2['id']
    if data_2['id'] not in reservation_ids:
        reservation_ids.append(data_2['id'])
    assert isinstance(data_2['id'], int)
    assert data_2['id'] == data['id']
    assert data_2['id'] > 0
    assert data_2['customerId'] == customer_id
    assert data_2['restaurantId'] == payload['restaurantId']
    assert data_2['tableId'] == payload['tableId']
    assert data_2['reservationDate'] == payload['reservationDate']
    assert data_2['reservationTime'] == payload['reservationTime']
    assert data_2['numberOfGuests'] == payload['numberOfGuests']
    assert data_2['status'] == 'PENDING'



def test_same_key_with_different_payload_returns_409(
    base_url, login_data, reservation_ids
):
    key = uuid4().hex
    headers = {'Authorization': f'Bearer {login_data['accessToken']}', 'Idempotency-Key': key}
    customer_id = login_data['customerId']
    payload = {'restaurantId': 1, 'customerId': customer_id, 'tableId': 1, 'reservationDate': (date.today() + timedelta(days=1)).isoformat(), 'reservationTime': '18:00:00', 'numberOfGuests': 1}
    payload_2 = payload.copy()
    payload_2["numberOfGuests"] = 2
    response = requests.post(f'{base_url}/api/reservations', headers=headers, timeout=10, json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    reservation_id = data['id']
    reservation_ids.append(reservation_id)
    assert isinstance(data['id'], int)
    assert data['id'] > 0
    assert data['customerId'] == customer_id
    assert data['restaurantId'] == payload['restaurantId']
    assert data['tableId'] == payload['tableId']
    assert data['reservationDate'] == payload['reservationDate']
    assert data['reservationTime'] == payload['reservationTime']
    assert data['numberOfGuests'] == payload['numberOfGuests']
    assert data['status'] == 'PENDING'
    response_reservation = requests.get(f'{base_url}/api/reservations/{reservation_id}', headers=headers, timeout=10)
    assert response_reservation.status_code == 200
    assert response_reservation.json()['status'] == 'PENDING'
    response_2 = requests.post(f'{base_url}/api/reservations', headers=headers, timeout=10, json=payload_2)
    if response_2.status_code == 201:
        second_id = response_2.json()["id"]
        if second_id not in reservation_ids:
            reservation_ids.append(second_id)
    assert response_2.status_code == 409, response_2.text
    assert 'Idempotency-Key was already used for a different reservation request' in response_2.json()['message']
    
    

    

