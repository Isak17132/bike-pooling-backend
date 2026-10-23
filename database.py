from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Isak@123 ko Isak%40123 likha gaya hai taaki URL format break na ho
DATABASE_URL = "postgresql+psycopg2://postgres:Isak%40123@localhost/bike_pooling_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()