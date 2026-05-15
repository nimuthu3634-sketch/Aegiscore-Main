from sqlalchemy import create_engine

from app.core.config import get_settings

# Creates the database engine used by the worker to check database access.
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
