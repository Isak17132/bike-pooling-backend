import bcrypt
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "bike_pooling_super_secret_key"
ALGORITHM = "HS256"

def hash_password(password: str):
    # Password ko pehle bytes me convert karna padta hai
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8') # Database me string save karne ke liye

def verify_password(plain_password: str, hashed_password: str):
    # Dono passwords ko match karne ke liye bytes me convert karna zaroori hai
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=1440)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt