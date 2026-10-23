from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    is_rider: bool = False

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    is_rider: bool
    class Config:
        from_attributes = True

class RideCreate(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    departure_time: datetime

class RideOut(BaseModel):
    id: int
    rider_id: int
    status: str
    departure_time: datetime
    class Config:
        from_attributes = True

class RideRequestOut(BaseModel):
    id: int
    ride_id: int
    commuter_id: int
    status: str
    class Config:
        from_attributes = True

        from typing import Optional

class ReviewCreate(BaseModel):
    rating: int
    comment: Optional[str] = None

class ReviewOut(BaseModel):
    id: int
    ride_id: int
    rating: int
    comment: Optional[str] = None

    class Config:
        from_attributes = True