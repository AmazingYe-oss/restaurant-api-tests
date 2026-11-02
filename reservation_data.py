"""Build editable reservation payloads for the local practice environment."""
from datetime import date, timedelta


def build_reservation_payload(
    customer_id,
    restaurant_id=1,
    table_id=1,
    reservation_date=None,
    reservation_time="18:00:00",
    number_of_guests=2,
):
    if reservation_date is None:
        reservation_date = (date.today() + timedelta(days=1)).isoformat()
    return {
        "restaurantId": restaurant_id,
        "customerId": customer_id,
        "tableId": table_id,
        "reservationDate": reservation_date,
        "reservationTime": reservation_time,
        "numberOfGuests": number_of_guests,
    }
