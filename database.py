

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Yeh line pehle cloud ka URL check karegi, agar nahi mila toh local use karegi
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Isak%40123@localhost/bike_pooling_db")


# (Yahan 'postgres:password' aur 'bikepool' ki jagah apni purani local details hi rehne dena)

# Render ka ek chota sa fix (postgres:// ko postgresql:// banata hai)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()