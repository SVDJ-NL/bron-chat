from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

# Configure the connection pool
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Increase from default of 5
    max_overflow=30,  # Increase from default of 10
    pool_timeout=60,  # Increase timeout
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600  # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from .models import Session  # Import Session model here to avoid circular imports
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
