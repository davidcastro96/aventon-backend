import uuid
import enum
from sqlalchemy import (
    Column,
    String,
    TIMESTAMP,
    ForeignKey,
    Integer,
    Boolean,
    DECIMAL,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    vehicles = relationship("Vehicle", back_populates="owner")
    driven_routes = relationship("Route", back_populates="driver")
    bookings = relationship("Booking", back_populates="passenger")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    color = Column(String, nullable=False)
    license_plate = Column(String, unique=True, nullable=False)

    owner = relationship("User", back_populates="vehicles")
    routes = relationship("Route", back_populates="vehicle")

class RouteStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    full = "full"
    completed = "completed"

class Route(Base):
    __tablename__ = "routes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    departure_time = Column(TIMESTAMP, nullable=False)
    estimated_arrival_time = Column(TIMESTAMP, nullable=False)
    available_seats = Column(Integer, nullable=False)
    price_per_seat = Column(DECIMAL(10, 2), nullable=False)
    is_recurrent = Column(Boolean, default=False)
    recurrence_pattern = Column(JSONB, nullable=True)
    status = Column(Enum(RouteStatus), default=RouteStatus.active)
    path = Column(Geometry(geometry_type='LINESTRING', srid=4326), nullable=False)

    driver = relationship("User", back_populates="driven_routes")
    vehicle = relationship("Vehicle", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route")
    bookings = relationship("Booking", back_populates="route")

class RouteStop(Base):
    __tablename__ = "route_stops"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    order = Column(Integer, nullable=False)

    route = relationship("Route", back_populates="stops")

class BookingStatus(str, enum.Enum):
    confirmed = "confirmed"
    cancelled_by_passenger = "cancelled_by_passenger"
    completed = "completed"

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    pickup_point = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    dropoff_point = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.confirmed)
    booked_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    passenger = relationship("User", back_populates="bookings")
    route = relationship("Route", back_populates="bookings")
