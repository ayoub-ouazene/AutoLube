import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to the project root .env file."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # Neon closes idle connections; this retries them
    pool_recycle=300,       # recycle every 5 min to stay under Neon's idle timeout
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
