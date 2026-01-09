from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.elements import WKBElement
from typing import List, Optional
from app.db import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user
from app.services.geolocation import get_location_details

router = APIRouter()

@router.post("/", response_model=schemas.RouteResponse, status_code=201)
def create_route(
    route: schemas.RouteCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validar que el vehicle_id pertenezca al usuario actual
    vehicle = db.query(models.Vehicle).filter(
        models.Vehicle.id == route.vehicle_id,
        models.Vehicle.owner_id == current_user.id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or does not belong to the current user")

    # Obtener precio por km
    price_per_km = route.price_per_km
    if price_per_km is None:
        default_price_config = db.query(models.SystemConfig).filter(models.SystemConfig.key == 'default_price_per_km_cop').first()
        if not default_price_config:
            raise HTTPException(status_code=500, detail="Default price per km is not configured")
        price_per_km = float(default_price_config.value)

    # Obtener detalles de localización (simulado)
    start_coords = route.path.coordinates[0]
    end_coords = route.path.coordinates[-1]
    start_location = get_location_details(lon=start_coords[0], lat=start_coords[1])
    end_location = get_location_details(lon=end_coords[0], lat=end_coords[1])

    # Convertir Pydantic schema a un objeto WKBElement para GeoAlchemy2
    coordinates_str = ", ".join([f"{p[0]} {p[1]}" for p in route.path.coordinates])
    path_wkb = WKBElement(f'SRID=4326;LINESTRING({coordinates_str})', extended=True)

    db_route = models.Route(
        driver_id=current_user.id,
        vehicle_id=route.vehicle_id,
        departure_time=route.departure_time,
        estimated_arrival_time=route.estimated_arrival_time,
        available_seats=route.available_seats,
        price_per_km=price_per_km,
        path=path_wkb,
        start_city=start_location['city'],
        start_country=start_location['country'],
        end_city=end_location['city'],
        end_country=end_location['country']
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

@router.get("/search", response_model=List[schemas.RouteResponse])
def search_routes(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user), # Asegurarse que el usuario está logueado
    buffer_meters: Optional[int] = 500 # Radio de búsqueda alrededor de los puntos
):
    """
    Busca rutas que pasen cerca de los puntos de origen y destino especificados por el pasajero.
    """
    # Convertir los puntos de origen y destino del pasajero a objetos PostGIS POINT
    passenger_origin = func.ST_SetSRID(func.ST_MakePoint(from_lon, from_lat), 4326)
    passenger_destination = func.ST_SetSRID(func.ST_MakePoint(to_lon, to_lat), 4326)

    # Realizar la búsqueda geoespacial
    routes = db.query(models.Route).filter(
        models.Route.available_seats > 0,
        models.Route.status == models.RouteStatus.active,
        # La ruta debe pasar cerca del origen del pasajero
        func.ST_DWithin(models.Route.path, passenger_origin, buffer_meters),
        # La ruta debe pasar cerca del destino del pasajero
        func.ST_DWithin(models.Route.path, passenger_destination, buffer_meters)
    ).all()

    if not routes:
        raise HTTPException(status_code=404, detail="No se encontraron rutas que cumplan los criterios.")
    
    return routes
