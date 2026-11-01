import os
from datetime import date, timedelta
import requests
from uuid import uuid4

def test_create_reservation_returns_201(login_data,base_url):
    token = login_data["accessToken"]
    customer_id = login_data["customerId"]

    payload = {
        "restaurantId": 1,
        "customerId": customer_id,
        "tableId": 1,
        "reservationDate": (date.today() + timedelta(days=1)).isoformat(),
        "reservationTime": "18:00:00",
        "numberOfGuests": 2,
    }


    response = requests.post(
            f"{base_url}/api/reservations",
            headers={"Authorization": f"Bearer {token}",
                     "Idempotency-Key": uuid4().hex,
                     },
            timeout=10,
            json=payload
        )



    assert response.status_code == 201, response.text
    data = response.json()
    reservation_id = data["id"]
    cancelled = False

    try:
        assert isinstance(data["id"], int)
        assert data["id"] > 0
        assert data["customerId"] == customer_id
        assert data["restaurantId"] == payload["restaurantId"]
        assert data["tableId"] == payload["tableId"]
        assert data["reservationDate"] == payload["reservationDate"]
        assert data["reservationTime"] == payload["reservationTime"]
        assert data["numberOfGuests"] == payload["numberOfGuests"]
        assert data["status"] == "PENDING"
        response_reservation=requests.get(
                f"{base_url}/api/reservations/{reservation_id}",
                headers = {"Authorization": f"Bearer {token}"}
            , timeout=10)

        assert response_reservation.status_code==200
        assert response_reservation.json()['status']=='PENDING'

        response_delete=requests.delete(
            f"{base_url}/api/reservations/{reservation_id}",
            headers = {"Authorization": f"Bearer {token}"}
        , timeout=10)
        assert response_delete.status_code==204

        cancelled=True
        response_get=requests.get(
         f"{base_url}/api/reservations/{reservation_id}",
                headers = {"Authorization": f"Bearer {token}"}
            , timeout=10)

        assert response_get.status_code==200
        assert response_get.json()['status']=='CANCELLED'

    finally:
        if not cancelled:
            try:
                cleanup_response = requests.delete(
                    f"{base_url}/api/reservations/{reservation_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                if cleanup_response.status_code != 204:
                    print(
                        "清理预约失败：",
                        cleanup_response.status_code,
                        cleanup_response.text,
                    )
            except requests.RequestException as error:
                print("清理预约时请求失败：", error)
