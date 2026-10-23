from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, security
from database import engine, SessionLocal
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import func
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
# Yeh code frontend ko backend se data lene ki permission deta hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local testing ke liye sabko allow kar rahe hain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"status": "Success", "message": "Welcome to P2P Bike Pooling Backend!"}

@app.post("/signup", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Yeh email pehle se registered hai!")
    
    hashed_pw = security.hash_password(user.password)
    new_user = models.User(
        full_name=user.full_name, email=user.email, 
        hashed_password=hashed_pw, is_rider=user.is_rider
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Galat email ya password!")
    
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Invalid ya Expired Token!")
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/me")
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "message": f"Welcome {current_user.full_name}, aapka lock perfectly kaam kar raha hai!", 
        "is_rider": current_user.is_rider
    }

@app.post("/rides", response_model=schemas.RideOut)
def create_ride(ride: schemas.RideCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_rider:
        raise HTTPException(status_code=403, detail="Aapki profile Rider ki nahi hai. Sirf riders hi ride bana sakte hain!")
    
    start_pt = f"POINT({ride.start_lng} {ride.start_lat})"
    end_pt = f"POINT({ride.end_lng} {ride.end_lat})"
    
    new_ride = models.Ride(
        rider_id=current_user.id,
        start_location=start_pt,
        end_location=end_pt,
        departure_time=ride.departure_time,
        status="active"
    )
    
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    return new_ride

@app.get("/rides/search", response_model=List[schemas.RideOut])
def search_nearby_rides(
    start_lat: float, 
    start_lng: float,
    end_lat: float, 
    end_lng: float,
    radius_km: float = 2.0,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    radius_m = radius_km * 1000
    
    search_start = f"POINT({start_lng} {start_lat})"
    search_end = f"POINT({end_lng} {end_lat})"
    
    nearby_rides = db.query(models.Ride).filter(
        models.Ride.status == "active",
        func.ST_DistanceSphere(models.Ride.start_location, func.ST_GeomFromText(search_start, 4326)) <= radius_m,
        func.ST_DistanceSphere(models.Ride.end_location, func.ST_GeomFromText(search_end, 4326)) <= radius_m
    ).all()
    
    return nearby_rides

@app.post("/rides/{ride_id}/request", response_model=schemas.RideRequestOut)
def request_ride(ride_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id, models.Ride.status == "active").first()
    if not ride:
        raise HTTPException(status_code=404, detail="Yeh ride ab available nahi hai.")
        
    if ride.rider_id == current_user.id:
        raise HTTPException(status_code=400, detail="Aap apni hi ride book nahi kar sakte.")
        
    existing_request = db.query(models.RideRequest).filter(
        models.RideRequest.ride_id == ride_id, 
        models.RideRequest.commuter_id == current_user.id
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Aapne pehle hi is ride ke liye request bhej di hai.")
        
    new_request = models.RideRequest(
        ride_id=ride_id,
        commuter_id=current_user.id,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    return new_request

# ------ RIDER ACTION ROUTE (Accept/Reject) ------

@app.put("/rides/requests/{request_id}", response_model=schemas.RideRequestOut)
def update_request_status(
    request_id: int, 
    action: str, # yahan hum 'accept' ya 'reject' bhejenge
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Request ko database me dhoondein
    ride_request = db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()
    if not ride_request:
        raise HTTPException(status_code=404, detail="Yeh request exist nahi karti.")
        
    # 2. Check karein ki jis Ride par request aayi hai, kya current_user hi uska asli Rider hai?
    ride = db.query(models.Ride).filter(models.Ride.id == ride_request.ride_id).first()
    if ride.rider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sirf bike ka owner hi request ko accept ya reject kar sakta hai.")
        
    # 3. Status update karein
    action = action.lower()
    if action == "accept":
        ride_request.status = "accepted"
    elif action == "reject":
        ride_request.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Action me sirf 'accept' ya 'reject' likhein.")
        
    db.commit()
    db.refresh(ride_request)
    
    return ride_request

# ------ RIDER KI PENDING REQUESTS DEKHNE KA ROUTE ------

@app.get("/rides/my-requests", response_model=List[schemas.RideRequestOut])
def get_my_pending_requests(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Rider ki apni rides par aayi hui sirf 'pending' requests nikalenge
    requests = db.query(models.RideRequest).join(models.Ride).filter(
        models.Ride.rider_id == current_user.id,
        models.RideRequest.status == "pending"
    ).all()
    
    return requests

# ------ RIDE STATUS UPDATE (Start, Complete, Cancel) ------

@app.put("/rides/{ride_id}/status", response_model=schemas.RideOut)
def update_ride_status(
    ride_id: int, 
    status: str, # yahan hum 'in_progress', 'completed', ya 'cancelled' bhejenge
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Ride ko database mein dhoondein
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Yeh ride nahi mili.")
        
    # 2. Check karein ki kya user is bike ka asli owner (Rider) hai
    if ride.rider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sirf bike owner hi apni ride ka status badal sakta hai.")
        
    # 3. Naye status ko validate aur update karein
    valid_statuses = ["active", "in_progress", "completed", "cancelled"]
    status = status.lower()
    
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status sirf inme se ek ho sakta hai: {', '.join(valid_statuses)}")
        
    ride.status = status
    db.commit()
    db.refresh(ride)
    
    return ride

# ------ MY TRIPS / RIDE HISTORY ROUTE ------

# ------ MY TRIPS / RIDE HISTORY ROUTE ------

@app.get("/users/me/history")
def get_my_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    # 1. User ne as a Rider kitni rides create ki hain
    rides_given = db.query(models.Ride).filter(
        models.Ride.rider_id == current_user.id
    ).order_by(models.Ride.departure_time.desc()).all()
    
    # 2. User ne as a Commuter kitni rides li hain (Jo requests accept ho chuki hain)
    rides_taken = db.query(models.Ride).join(models.RideRequest).filter(
        models.RideRequest.commuter_id == current_user.id,
        models.RideRequest.status == "accepted"
    ).order_by(models.Ride.departure_time.desc()).all()
    
    # FIX: WKBElement (GPS Map data) ko hata kar sirf zaroori details (ID, Status, Time) bhej rahe hain
    clean_rides_given = [{"id": r.id, "status": r.status, "departure_time": r.departure_time} for r in rides_given]
    clean_rides_taken = [{"id": r.id, "status": r.status, "departure_time": r.departure_time} for r in rides_taken]
    
    return {
        "user_name": current_user.full_name,
        "total_rides_given": len(rides_given),
        "total_rides_taken": len(rides_taken),
        "rides_given": clean_rides_given,
        "rides_taken": clean_rides_taken
    }

# ------ RATING & REVIEWS ROUTE ------

@app.post("/rides/{ride_id}/reviews", response_model=schemas.ReviewOut)
def create_review(ride_id: int, review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    # 1. Check karein ki ride completely khtam ho chuki hai
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride or ride.status != "completed":
        raise HTTPException(status_code=400, detail="Ride 'completed' hone ke baad hi review de sakte hain.")
        
    # 2. Check karein ki is commuter ne sach me yeh ride li thi
    valid_commuter = db.query(models.RideRequest).filter(
        models.RideRequest.ride_id == ride_id,
        models.RideRequest.commuter_id == current_user.id,
        models.RideRequest.status == "accepted"
    ).first()
    
    if not valid_commuter:
        raise HTTPException(status_code=403, detail="Aap is ride ka hissa nahi the, isliye review nahi de sakte.")
        
    # 3. Rating 1 se 5 ke beech honi chahiye
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating sirf 1 se 5 ke beech honi chahiye.")
        
    # 4. Database mein save karein
    new_review = models.Review(
        ride_id=ride_id,
        reviewer_id=current_user.id,
        rider_id=ride.rider_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return new_review

# ------ LIVE LOCATION (WEBSOCKETS) ------

# Yeh class track rakhegi ki kis ride par kitne log connected hain
class ConnectionManager:
    def __init__(self):
        # Format: { ride_id: [websocket_1, websocket_2, ...] }
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, ride_id: int):
        await websocket.accept()
        if ride_id not in self.active_connections:
            self.active_connections[ride_id] = []
        self.active_connections[ride_id].append(websocket)

    def disconnect(self, websocket: WebSocket, ride_id: int):
        if ride_id in self.active_connections:
            self.active_connections[ride_id].remove(websocket)
            if len(self.active_connections[ride_id]) == 0:
                del self.active_connections[ride_id]

    async def broadcast_location(self, ride_id: int, message: str):
        if ride_id in self.active_connections:
            for connection in self.active_connections[ride_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/rides/{ride_id}")
async def ride_live_location(websocket: WebSocket, ride_id: int):
    # 1. Jaise hi app khulegi, pipeline connect ho jayegi
    await manager.connect(websocket, ride_id)
    try:
        while True:
            # 2. Rider apni nayi Lat/Long is pipeline me daalega
            data = await websocket.receive_text()
            
            # 3. Server turant us location ko baki sabhi connected users (Commuter) ko bhej dega
            update_message = f"Live GPS [{ride_id}]: {data}"
            await manager.broadcast_location(ride_id, update_message)
            
    except WebSocketDisconnect:
        # 4. Agar internet disconnect hua toh pipeline band kar do
        manager.disconnect(websocket, ride_id)