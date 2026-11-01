"""Prepare reusable restaurant/table data; no reservations are created."""
import json
from pathlib import Path
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:18080"

def request(method, path, expected=200, **kwargs):
    response = requests.request(method, BASE + path, timeout=15, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(f"{method} {path}: expected {expected}, got {response.status_code}")
    return response.json()

def main():
    config = dotenv_values(ROOT / "deploy/.env")
    login = request("POST", "/api/auth/login", json={
        "email": config["APP_ADMIN_EMAIL"],
        "password": config["APP_ADMIN_PASSWORD"],
    })
    if login["role"] != "ADMIN":
        raise RuntimeError("Preparation account must be ADMIN")
    headers = {"Authorization": "Bearer " + login["accessToken"]}
    name = "Automation Practice Restaurant"
    restaurants = request("GET", "/api/restaurants")
    matches = [r for r in restaurants if r["name"] == name]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous practice restaurant; inspect data before continuing")
    restaurant = matches[0] if matches else request("POST", "/api/restaurants", 201,
        headers=headers, json={"name": name, "address": "Local Test Lab",
        "openingTime": "09:00:00", "closingTime": "22:00:00"})
    rid = restaurant["id"]
    tables = request("GET", f"/api/restaurants/{rid}/tables")
    matches = [t for t in tables if t["tableNumber"] == "AUTO-01"]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous practice table")
    table = matches[0] if matches else request("POST", f"/api/restaurants/{rid}/tables", 201,
        headers=headers, json={"tableNumber": "AUTO-01", "capacity": 4})
    assert restaurant["openingTime"] == "09:00:00"
    assert restaurant["closingTime"] == "22:00:00"
    assert table["capacity"] == 4 and table["restaurantId"] == rid
    evidence = {"restaurantId": rid, "restaurantName": name,
        "openingTime": restaurant["openingTime"], "closingTime": restaurant["closingTime"],
        "tableId": table["id"], "tableNumber": table["tableNumber"], "capacity": table["capacity"],
        "preparedBy": "AI via administrator API; not a learner-authored test"}
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence/reservation-data.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence))

if __name__ == "__main__":
    main()
