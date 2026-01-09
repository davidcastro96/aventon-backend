from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas import schemas
from app.models import models

from app.api.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/me/vehicles", response_model=schemas.VehicleResponse, status_code=201)
def create_vehicle_for_user(
    vehicle: schemas.VehicleCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    db_vehicle = models.Vehicle(**vehicle.model_dump(), owner_id=current_user.id)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@router.get("/me/vehicles", response_model=List[schemas.VehicleResponse])
def read_own_vehicles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Vehicle).filter(models.Vehicle.owner_id == current_user.id).all()

