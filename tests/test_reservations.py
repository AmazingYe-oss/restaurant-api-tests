from reservation_data import build_reservation_payload
from reservation_api import create_reservation, get_reservation, cancel_reservation
import os
from datetime import date, timedelta
import requests
from uuid import uuid4
import pytest
from concurrent.futures import ThreadPoolExecutor

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





def test_customer_cannot_cancel_another_reservation(base_url, login_data, register_user, reservation_ids):
    customer_id = login_data["customerId"]
    assert register_user["role"] == "CUSTOMER"
    assert register_user["customerId"] != customer_id
    token_a = login_data["accessToken"]
    token_b = register_user["accessToken"]
    payload = build_reservation_payload(customer_id)
    created = create_reservation(base_url, token_a, payload, uuid4().hex)
    assert created.status_code == 201, created.text
    reservation_id = created.json()["id"]
    reservation_ids.append(reservation_id)
    cancelled = cancel_reservation(base_url, token_b, reservation_id)
    assert cancelled.status_code == 403, cancelled.text
    queried = get_reservation(base_url, token_a, reservation_id)
    assert queried.status_code == 200, queried.text
    data = queried.json()
    assert data["id"] == reservation_id
    assert data["customerId"] == customer_id
    assert data["status"] == "PENDING"


def test_concurrent_reservations_allow_only_one(
    base_url, login_data, reservation_ids
):
    status=[]
    token = login_data["accessToken"]
    payload = build_reservation_payload(login_data["customerId"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(
            create_reservation,
            base_url, token, payload, uuid4().hex,
        )
        second = pool.submit(
            create_reservation,
            base_url, token, payload, uuid4().hex,
        )

        responses = [first.result(), second.result()]
    for response in responses:
        if response.status_code == 201:
            reservation_ids.append(response.json()["id"])
        status.append(response.status_code)

    assert sorted(status) == [201, 409], [
        (response.status_code, response.text) for response in responses
    ]

def test_reservation_with_past_date_returns_400(
    base_url, login_data, reservation_ids
):
    payload = build_reservation_payload(
    login_data["customerId"],
    reservation_date=(date.today() - timedelta(days=2)).isoformat(),
)
    response=create_reservation(base_url=base_url,payload=payload,idempotency_key=uuid4().hex,token=login_data['accessToken'])
    if response.status_code==201:
        reservation_ids.append(response.json()['id'])

    assert response.status_code==400, response.text
    assert "reservation date cannot be in the past" in (
    response.json()["message"].lower()
)


@pytest.mark.parametrize(
    "start_time, expected_status",
    [
        ("08:59:00", 400),
        ("09:00:00", 201),
        ("09:01:00", 201),
        ("19:59:00", 201),
        ("20:00:00", 201),
        ("20:01:00", 400),
    ],
)
def test_reservation_start_time_boundary(
    base_url, login_data, reservation_ids,
    start_time, expected_status,
):
    customer_id=login_data['customerId']
    access_token=login_data['accessToken']
    payload=build_reservation_payload(customer_id=customer_id,reservation_time=start_time)
    response=create_reservation(base_url=base_url,token=access_token,idempotency_key=uuid4().hex,payload=payload)
    if response.status_code==201:
        reservation_ids.append(response.json()['id'])
    assert response.status_code==expected_status
    assert response.status_code == expected_status, response.text
    data = response.json()

    if expected_status == 201:
        assert data["reservationTime"] == start_time
        assert data["status"] == "PENDING"
    else:
        assert data["status"] == 400
        assert data["path"] == "/api/reservations"



def test_pending_reservation_cannot_be_completed(
    base_url, login_data, admin_login_data, reservation_ids
):
    customer_id = login_data["customerId"]
    access_token = login_data["accessToken"]
    payload = build_reservation_payload(customer_id=customer_id)
    response = create_reservation(
        base_url=base_url,
        token=access_token,
        idempotency_key=uuid4().hex,
        payload=payload,
    )
    assert response.status_code == 201, response.text
    reservation_id = response.json()["id"]
    reservation_ids.append(reservation_id)

    admin_token = admin_login_data["accessToken"]
    complete_response = requests.put(
        f"{base_url}/api/reservations/{reservation_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "COMPLETED"},
        timeout=10,
    )
    assert complete_response.status_code == 400, complete_response.text
    assert "invalid status transition" in complete_response.json()["message"].lower()

    response_get = get_reservation(base_url, access_token, reservation_id)
    assert response_get.status_code == 200, response_get.text
    assert response_get.json()["status"] == "PENDING"

def test_reservation_can_be_confirmed_then_completed(
    base_url, login_data, admin_login_data, reservation_ids
):
    customer_id = login_data["customerId"]
    access_token = login_data["accessToken"]
    payload = build_reservation_payload(customer_id=customer_id)
    response = create_reservation(
        base_url=base_url,
        token=access_token,
        idempotency_key=uuid4().hex,
        payload=payload,
    )
    assert response.status_code == 201, response.text
    reservation_id = response.json()["id"]
    reservation_ids.append(reservation_id)

    admin_token = admin_login_data["accessToken"]
    assert response.json()["status"] == "PENDING"
    confirm_response = requests.put(
        f"{base_url}/api/reservations/{reservation_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CONFIRMED"},
        timeout=10,
    )
    assert confirm_response.status_code == 200, confirm_response.text
    assert confirm_response.json()["status"] == "CONFIRMED"

    complete_response = requests.put(
        f"{base_url}/api/reservations/{reservation_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "COMPLETED"},
        timeout=10,
    )
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["status"] == "COMPLETED"

    queried = get_reservation(base_url, access_token, reservation_id)
    assert queried.status_code == 200, queried.text
    data = queried.json()
    assert data["id"] == reservation_id
    assert data["status"] == "COMPLETED"
