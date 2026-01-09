from pydantic import BaseModel, EmailStr, UUID4, field_serializer
from typing import List, Optional, Any
from datetime import datetime
from shapely import wkb
from shapely.geometry import mapping
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID4
    profile_picture_url: Optional[str] = None
    created_at: datetime
    role: str

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

# Phone Verification Schemas
class PhoneVerificationRequest(BaseModel):
    phone_number: str

class PhoneVerificationResponse(BaseModel):
    phone_number: str
    otp_code: str # Se devuelve para simulación

class PhoneVerificationVerify(BaseModel):
    phone_number: str
    otp_code: str
    full_name: str

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
    price_per_km: Optional[float] = None

class RouteCreate(RouteBase):
    vehicle_id: UUID4
    stops: Optional[List[RouteStopBase]] = []
    path: LineStringGeometry

class RouteResponse(RouteBase):
    id: UUID4
    driver_id: UUID4
    vehicle_id: UUID4
    status: str
    start_city: Optional[str] = None
    start_country: Optional[str] = None
    end_city: Optional[str] = None
    end_country: Optional[str] = None
    path: Any

    @field_serializer('path')
    def serialize_path(self, path: Any, _info):
        if hasattr(path, 'data'):
            return mapping(wkb.loads(bytes(path.data)))
        return None

    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    route_id: UUID4
    pickup_point: PointGeometry
    dropoff_point: PointGeometry

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: UUID4
    passenger_id: UUID4
    status: str
    booked_at: datetime
    calculated_price: float

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentBase(BaseModel):
    amount: float
    currency: str
    status: str

class PaymentResponse(PaymentBase):
    id: UUID4
    booking_id: UUID
    payment_gateway_ref: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# System Config Schemas
class SystemConfigBase(BaseModel):
    key: str
    value: str

class SystemConfigUpdate(SystemConfigBase):
    pass

class SystemConfigResponse(SystemConfigBase):
    class Config:
        from_attributes = True