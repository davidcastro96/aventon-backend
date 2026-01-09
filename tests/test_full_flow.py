import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import models
import uuid
import decimal

# --- Fixtures de Datos de Prueba ---

@pytest.fixture(scope="function") # Scope function para limpiar por cada test
def test_driver_user(client: TestClient, db_session: Session):
    """Crea un usuario conductor para las pruebas y asegura que no exista."""
    phone_number = "3201112233"
    db_session.query(models.User).filter_by(phone_number=phone_number).delete()
    db_session.query(models.PhoneVerification).filter_by(phone_number=phone_number).delete()
    db_session.commit()

    response = client.post("/auth/otp/request", json={"phone_number": phone_number})
    otp_code = response.json()["otp_code"]
    response = client.post("/auth/otp/verify", json={
        "phone_number": phone_number,
        "otp_code": otp_code,
        "full_name": "Conductor de Prueba Flujo"
    })
    token = response.json()["access_token"]
    # Obtener el user_id del usuario creado
    user = db_session.query(models.User).filter_by(phone_number=phone_number).first()
    return {"phone": phone_number, "name": "Conductor de Prueba Flujo", "token": token, "id": str(user.id)}

@pytest.fixture(scope="function") # Scope function para limpiar por cada test
def test_passenger_user(client: TestClient, db_session: Session):
    """Crea un usuario pasajero para las pruebas y asegura que no exista."""
    phone_number = "3214445566"
    db_session.query(models.User).filter_by(phone_number=phone_number).delete()
    db_session.query(models.PhoneVerification).filter_by(phone_number=phone_number).delete()
    db_session.commit()

    response = client.post("/auth/otp/request", json={"phone_number": phone_number})
    otp_code = response.json()["otp_code"]
    response = client.post("/auth/otp/verify", json={
        "phone_number": phone_number,
        "otp_code": otp_code,
        "full_name": "Pasajero de Prueba Flujo"
    })
    token = response.json()["access_token"]
    user = db_session.query(models.User).filter_by(phone_number=phone_number).first()
    return {"phone": phone_number, "name": "Pasajero de Prueba Flujo", "token": token, "id": str(user.id)}


# --- Pruebas del Flujo Completo ---

def test_full_booking_flow(client: TestClient, db_session: Session, test_driver_user, test_passenger_user):
    """
    Prueba el flujo end-to-end:
    1. Conductor crea un vehículo.
    2. Conductor crea una ruta.
    3. Pasajero busca la ruta.
    4. Pasajero solicita una reserva (booking).
    5. Pasajero paga la reserva.
    6. Se verifica que el asiento fue descontado y los estados actualizados.
    """
    driver_token = test_driver_user["token"]
    passenger_token = test_passenger_user["token"]

    # Asegurar que el precio por km por defecto exista
    default_price_config = db_session.query(models.SystemConfig).filter_by(key='default_price_per_km_cop').first()
    if not default_price_config:
        db_session.add(models.SystemConfig(key='default_price_per_km_cop', value='350.0'))
        db_session.commit()
    
    # 1. Conductor crea un vehículo
    vehicle_response = client.post(
        "/users/me/vehicles",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={"brand": "TestCar", "model": "Model-T", "color": "Black", "license_plate": f"TEST-{uuid.uuid4().hex[:5]}"}
    )
    assert vehicle_response.status_code == 201, vehicle_response.json()
    vehicle_id = vehicle_response.json()["id"]

    # 2. Conductor crea una ruta
    route_payload = {
        "departure_time": "2026-05-01T08:00:00Z",
        "estimated_arrival_time": "2026-05-01T09:00:00Z",
        "available_seats": 1, # Solo 1 asiento para probar el descuento
        "price_per_km": 500.0, # 500 COP por km
        "vehicle_id": vehicle_id,
        "path": { # Coordenadas para una ruta en Cali, Colombia
            "type": "LineString",
            "coordinates": [
                [-76.53676, 3.42158], # Punto A (Cali)
                [-76.53000, 3.42500], # Punto intermedio
                [-76.52000, 3.43000]  # Punto B (Cali)
            ]
        }
    }
    route_response = client.post(
        "/routes",
        headers={"Authorization": f"Bearer {driver_token}"},
        json=route_payload
    )
    assert route_response.status_code == 201, route_response.json()
    route_id = route_response.json()["id"]
    initial_available_seats = route_response.json()["available_seats"]
    
    # 3. Pasajero busca la ruta
    # Usamos coordenadas que estan cerca del path de la ruta creada
    search_response = client.get(
        "/routes/search",
        headers={"Authorization": f"Bearer {passenger_token}"},
        params={
            "from_lat": 3.421, "from_lon": -76.536, # Cerca del punto A
            "to_lat": 3.430, "to_lon": -76.520,   # Cerca del punto B
            "buffer_meters": 1000
        }
    )
    assert search_response.status_code == 200, search_response.json()
    assert len(search_response.json()) > 0
    found_route_ids = [r["id"] for r in search_response.json()]
    assert route_id in found_route_ids

    # 4. Pasajero solicita una reserva (booking)
    # Puntos de recogida y bajada a lo largo de la ruta
    booking_payload = {
        "route_id": route_id,
        "pickup_point": {"type": "Point", "coordinates": [-76.53676, 3.42158]}, # Punto A
        "dropoff_point": {"type": "Point", "coordinates": [-76.52000, 3.43000]} # Punto B
    }
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {passenger_token}"},
        json=booking_payload
    )
    assert booking_response.status_code == 201, booking_response.json()
    booking_id = booking_response.json()["id"]
    calculated_price = booking_response.json()["calculated_price"]
    assert booking_response.json()["status"] == "pending"
    # El precio calculado debería ser > 0 y razonable para la distancia entre los puntos
    assert calculated_price > 0
    # Ejemplo: distancia aproximada entre esos puntos es ~2.2km, * 500 = 1100
    assert decimal.Decimal(calculated_price) == pytest.approx(decimal.Decimal("1100.00"), abs=50)


    # 5. Pasajero paga la reserva
    pay_response = client.post(
        f"/bookings/{booking_id}/pay",
        headers={"Authorization": f"Bearer {passenger_token}"}
    )
    assert pay_response.status_code == 200, pay_response.json()
    assert pay_response.json()["status"] == "completed"
    assert pay_response.json()["booking_id"] == booking_id
    assert pay_response.json()["amount"] == calculated_price

    # 6. Verificar que el asiento fue descontado y los estados actualizados
    # Obtener la ruta nuevamente para verificar asientos
    # Necesitaríamos un GET /routes/{route_id} para una verificación completa.
    # Por ahora, verificamos el booking directamente.
    booking_from_db = db_session.query(models.Booking).get(booking_id)
    assert booking_from_db.status == models.BookingStatus.confirmed
    route_from_db = db_session.query(models.Route).get(route_id)
    assert route_from_db.available_seats == initial_available_seats - 1