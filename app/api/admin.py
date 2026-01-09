from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import models
from app.schemas import schemas
from app.api.auth import get_current_user

router = APIRouter()

# Dependencia para verificar que el usuario es Admin
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user

@router.put("/config", response_model=schemas.SystemConfigResponse)
def update_system_config(
    config_in: schemas.SystemConfigUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """
    Actualiza una configuración del sistema.
    Solo accesible por administradores.
    """
    config_item = db.query(models.SystemConfig).filter(models.SystemConfig.key == config_in.key).first()
    if not config_item:
        raise HTTPException(status_code=404, detail=f"Config key '{config_in.key}' not found")
    
    config_item.value = config_in.value
    db.commit()
    db.refresh(config_item)
    return config_item

@router.get("/config", response_model=List[schemas.SystemConfigResponse])
def get_system_configs(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """
    Obtiene todas las configuraciones del sistema.
    Solo accesible por administradores.
    """
    return db.query(models.SystemConfig).all()
