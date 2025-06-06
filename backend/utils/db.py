# backend/common/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.config import DATABASE_URL

# Create engine with appropriate connect_args based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite only
    )
else:
    engine = create_engine(DATABASE_URL)  # PostgreSQL, MySQL, etc.
SessionLocal = sessionmaker(
    autoflush=False, autocommit=False, bind=engine
)
Base = declarative_base()