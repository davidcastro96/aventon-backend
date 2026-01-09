from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.RouteResponse, status_code=201)
def create_route(
    route: schemas.RouteCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Convert Pydantic schema to a dictionary for GeoAlchemy2
    path_dict = route.path.model_dump()

    db_route = models.Route(
        driver_id=current_user.id,
        vehicle_id=route.vehicle_id,
        departure_time=route.departure_time,
        estimated_arrival_time=route.estimated_arrival_time,
        available_seats=route.available_seats,
        price_per_seat=route.price_per_seat,
        path=f'SRID=4326;{path_dict["type"].upper()}({",".join([f"{p[0]} {p[1]}" for p in path_dict["coordinates"]])})'
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
    db: Session = Depends(get_db)
):
    """
    Searches for routes that pass near the origin and destination points.
    
    This is a placeholder and needs to be implemented with a proper geospatial query.
    """
    # Pseudo-query - requires raw SQL with PostGIS functions for efficiency
    # from sqlalchemy import text
    # result = db.execute(text("... use ST_DWithin ..."))
    
    # For now, return all routes as a placeholder
    routes = db.query(models.Route).filter(models.Route.status == 'active').all()
    if not routes:
        raise HTTPException(status_code=404, detail="No routes found")
    return routes
