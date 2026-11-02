"""Reservation HTTP requests; business assertions belong in tests."""
import requests

def create_reservation(base_url, token, payload, idempotency_key):
    return requests.post(
        f"{base_url}/api/reservations",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key},
        json=payload, timeout=10,
    )

def get_reservation(base_url, token, reservation_id):
    return requests.get(
        f"{base_url}/api/reservations/{reservation_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )

def cancel_reservation(base_url, token, reservation_id):
    return requests.delete(
        f"{base_url}/api/reservations/{reservation_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=10,
    )
