from pydantic import BaseModel, EmailStr, UUID4, computed_field
from typing import List, Optional, Any
from datetime import datetime
from shapely import wkb
from shapely.geometry import mapping

# User Schemas
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID4
    profile_picture_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Vehicle Schemas
class VehicleBase(BaseModel):
    brand: str
    model: str
    color: str
    license_plate: str

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: UUID4
    owner_id: UUID4

    class Config:
        from_attributes = True

# GeoJSON Schemas for API validation
class PointGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float] # [longitude, latitude]

class LineStringGeometry(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]] # [[lon, lat], [lon, lat], ...]

# Route Schemas
class RouteStopBase(BaseModel):
    location: PointGeometry
    order: int

class RouteBase(BaseModel):
    departure_time: datetime
    estimated_arrival_time: datetime
    available_seats: int
    price_per_seat: float
    # El path se mueve al response para serialización custom
    # path: LineStringGeometry 

class RouteCreate(RouteBase):
    vehicle_id: UUID4
    stops: Optional[List[RouteStopBase]] = []
    path: LineStringGeometry # Se mantiene aquí para la creación

class RouteResponse(RouteBase):
    id: UUID4
    driver_id: UUID4
    vehicle_id: UUID4
    status: str
    
    @computed_field
    @property
    def path(self) -> Any:
        # Convierte el objeto WKBElement de la BD a un diccionario GeoJSON
        return mapping(wkb.loads(bytes(self.path.data)))

    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    pickup_point: PointGeometry
    dropoff_point: PointGeometry

class BookingCreate(BookingBase):
    route_id: UUID4

class BookingResponse(BookingBase):
    id: UUID4
    passenger_id: UUID4
    route_id: UUID4
    status: str
    booked_at: datetime

    class Config:
        from_attributes = True
