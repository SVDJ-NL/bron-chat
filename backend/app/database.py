from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings
import logging

logger = logging.getLogger(__name__)

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
    from .models import Session, Feedback
    
    def table_exists(table_name):
        try:
            with engine.connect() as conn:
                return engine.dialect.has_table(conn, table_name)
        except Exception:
            return False
    
    try:
        # Only create tables that don't exist
        tables_to_create = [table for table in Base.metadata.tables.values()
                          if not table_exists(table.name)]
        if tables_to_create:
            Base.metadata.create_all(bind=engine, tables=tables_to_create)
            logger.info(f"Created tables: {[t.name for t in tables_to_create]}")
        else:
            logger.info("All tables already exist")
    except Exception as e:
        logger.warning(f"Error during database initialization: {str(e)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
