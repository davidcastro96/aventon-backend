from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.elements import WKBElement
from typing import List
import uuid

from app.db import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crea una solicitud de reserva para una ruta.
    Calcula el precio basado en la distancia a recorrer sobre el path de la ruta.
    La reserva se crea en estado 'pending' hasta que se procesa el pago.
    """
    route = db.query(models.Route).filter(models.Route.id == booking_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    if route.status != models.RouteStatus.active:
        raise HTTPException(status_code=400, detail="Route is not active")
    if route.available_seats <= 0:
        raise HTTPException(status_code=400, detail="No available seats")

    # --- Lógica de Cálculo de Precio ---
    # 1. Proyectar los puntos de subida/bajada del pasajero sobre la línea de la ruta
    # 2. Crear una sub-línea (un recorte) del path de la ruta entre esos dos puntos
    # 3. Calcular la longitud de esa sub-línea en metros y convertir a km
    # 4. Multiplicar por el precio/km de la ruta

    # Esta es una consulta SQL compleja que usa funciones de PostGIS
    sql_query = text("""
        WITH
        line AS (SELECT path FROM routes WHERE id = :route_id),
        start_point AS (SELECT ST_SetSRID(ST_MakePoint(:start_lon, :start_lat), 4326) as geom),
        end_point AS (SELECT ST_SetSRID(ST_MakePoint(:end_lon, :end_lat), 4326) as geom),
        
        start_fraction AS (SELECT ST_LineLocatePoint(line.path, start_point.geom) as fraction FROM line, start_point),
        end_fraction AS (SELECT ST_LineLocatePoint(line.path, end_point.geom) as fraction FROM line, end_point),

        subline AS (
            SELECT ST_LineSubstring(line.path, LEAST(start_fraction.fraction, end_fraction.fraction), GREATEST(start_fraction.fraction, end_fraction.fraction)) as segment
            FROM line, start_fraction, end_fraction
        )

        SELECT ST_Length(segment::geography) / 1000.0 as distance_km FROM subline;
    """)

    result = db.execute(sql_query, {
        "route_id": str(route.id),
        "start_lon": booking_in.pickup_point.coordinates[0],
        "start_lat": booking_in.pickup_point.coordinates[1],
        "end_lon": booking_in.dropoff_point.coordinates[0],
        "end_lat": booking_in.dropoff_point.coordinates[1],
    }).first()

    if not result or result.distance_km is None:
        raise HTTPException(status_code=400, detail="Could not calculate distance along route. Ensure pickup/dropoff points are near the route path.")

    distance_km = result.distance_km
    calculated_price = float(distance_km) * float(route.price_per_km)

    # Convertir puntos de entrada a WKBElement para guardar en la BD
    pickup_wkb = WKBElement(f'SRID=4326;POINT({booking_in.pickup_point.coordinates[0]} {booking_in.pickup_point.coordinates[1]})', extended=True)
    dropoff_wkb = WKBElement(f'SRID=4326;POINT({booking_in.dropoff_point.coordinates[0]} {booking_in.dropoff_point.coordinates[1]})', extended=True)

    db_booking = models.Booking(
        passenger_id=current_user.id,
        route_id=booking_in.route_id,
        pickup_point=pickup_wkb,
        dropoff_point=dropoff_wkb,
        calculated_price=calculated_price
        # El status por defecto es 'pending'
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking

@router.post("/{booking_id}/pay", response_model=schemas.PaymentResponse)
def pay_for_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Simula el pago de una reserva pendiente.
    Esta operación es atómica: descuenta el asiento y confirma la reserva.
    """
    with db.begin_nested(): # Inicia un SAVEPOINT para la transacción
        booking = db.query(models.Booking).filter(
            models.Booking.id == booking_id,
            models.Booking.passenger_id == current_user.id
        ).first()

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or you don't have access to it")
        if booking.status != models.BookingStatus.pending:
            raise HTTPException(status_code=400, detail=f"Booking is not pending. Current status: {booking.status}")

        # Bloquear la fila de la ruta para evitar que dos personas reserven el último asiento a la vez
        route = db.query(models.Route).filter(models.Route.id == booking.route_id).with_for_update().one()

        if route.available_seats <= 0:
            raise HTTPException(status_code=400, detail="No more available seats on this route")

        # Todo en orden, proceder con la reserva y pago (simulado)
        route.available_seats -= 1
        booking.status = models.BookingStatus.confirmed

        db_payment = models.Payment(
            booking_id=booking.id,
            amount=booking.calculated_price,
            status=models.PaymentStatus.completed,
            payment_gateway_ref=f"sim_{uuid.uuid4()}" # ID de transacción simulado
        )
        db.add(db_payment)
        db.commit()
    
    db.refresh(db_payment)
    return db_payment
