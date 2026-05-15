from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Creates the database engine using the configured database URL.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is used whenever the API needs to talk with the database.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db_session():
    # Provides a database session for FastAPI routes and closes it after use.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()