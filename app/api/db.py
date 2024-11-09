import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import asyncio
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise HTTPException(status_code=500, detail="DATABASE_URL is not set.")

# Initialize the database engine and sessionmaker
engine = create_async_engine(DATABASE_URL, echo=True, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency for getting a database session
async def get_db_connection():
    """Provide a database session from the pool."""
    async with SessionLocal() as session:
        yield session

# Initialization and cleanup of database pool (not necessary for SQLAlchemy since it's managed automatically)
async def init_db_pool():
    """Initialize the database connection pool."""
    # No additional setup required for SQLAlchemy since it's handled by the engine
    logging.debug("Database pool initialized")

async def close_db_pool():
    """Close the database connection pool."""
    await engine.dispose()
    logging.debug("Database pool closed")
