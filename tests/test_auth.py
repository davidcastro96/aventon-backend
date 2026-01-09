from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import models

def test_request_otp(client: TestClient, db_session: Session):
    """Prueba que se puede solicitar un código OTP."""
    # Limpiar cualquier usuario o verificación existente para el número de teléfono
    db_session.query(models.PhoneVerification).filter_by(phone_number="3101234567").delete()
    db_session.query(models.User).filter_by(phone_number="3101234567").delete()
    db_session.commit()

    response = client.post("/auth/otp/request", json={"phone_number": "3101234567"})
    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == "3101234567"
    assert "otp_code" in data
    assert len(data["otp_code"]) == 6

def test_verify_otp_and_register(client: TestClient, db_session: Session):
    """Prueba el flujo completo de registro por teléfono."""
    phone_number = "3109876543"
    # Limpiar antes de la prueba
    db_session.query(models.PhoneVerification).filter_by(phone_number=phone_number).delete()
    db_session.query(models.User).filter_by(phone_number=phone_number).delete()
    db_session.commit()

    # 1. Solicitar OTP
    response = client.post("/auth/otp/request", json={"phone_number": phone_number})
    assert response.status_code == 200
    otp_code = response.json()["otp_code"]

    # 2. Verificar OTP y registrar usuario
    response = client.post(
        "/auth/otp/verify",
        json={
            "phone_number": phone_number,
            "otp_code": otp_code,
            "full_name": "Pasajero de Prueba OTP"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verificar que el usuario fue creado
    user = db_session.query(models.User).filter_by(phone_number=phone_number).first()
    assert user is not None
    assert user.full_name == "Pasajero de Prueba OTP"