from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_rider = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

class Ride(Base):
    __tablename__ = "rides"
    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id"))
    start_location = Column(Geometry(geometry_type='POINT', srid=4326))
    end_location = Column(Geometry(geometry_type='POINT', srid=4326))
    departure_time = Column(DateTime)
    status = Column(String, default="active")
    rider = relationship("User")

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    commuter_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    ride = relationship("Ride")
    commuter = relationship("User")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    rider_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(String, nullable=True)
    ride = relationship("Ride")