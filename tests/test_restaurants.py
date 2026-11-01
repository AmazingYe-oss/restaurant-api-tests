import requests


def test_get_restaurants_returns_list(base_url):
    response = requests.get(
        f"{base_url}/api/restaurants",
        timeout=10,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_restaurant_returns_404(base_url):
    response = requests.get(
        f"{base_url}/api/restaurants/999",
        timeout=10,
    )

    assert response.status_code == 404
    assert response.json()["path"] == '/api/restaurants/999'
