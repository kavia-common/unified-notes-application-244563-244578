"""
Database connection/session for FastAPI backend, using environment variables.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = os.environ.get("POSTGRES_URL")  # should be e.g. postgresql://user:pass@host:port/db
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")

# If POSTGRES_URL contains a full URL (starts with postgresql://), use it directly.
if POSTGRES_URL and POSTGRES_URL.startswith("postgresql://"):
    DATABASE_URL = POSTGRES_URL
else:
    # Compose from parts if not already a URI
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db():
    """Yields a SQLAlchemy session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
