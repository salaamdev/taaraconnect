from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

# Use SQLite for easier setup - can be changed to PostgreSQL later
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taara_monitoring.db")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DataUsageRecord(Base):
    __tablename__ = "data_usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Bundle Information
    subscriber_id = Column(String, nullable=False)
    plan_name = Column(String, nullable=False)
    plan_id = Column(String, nullable=False)
    
    # Usage Data
    remaining_balance_gb = Column(Float, nullable=False)
    remaining_balance_bytes = Column(BigInteger, nullable=False)
    total_data_usage_bytes = Column(BigInteger, nullable=False)
    expires_in_days = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, nullable=False)
    is_home_plan = Column(Boolean, default=False)
    
    # Raw response for debugging
    raw_response = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())

class ApiLog(Base):
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
