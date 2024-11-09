import asyncpg
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise HTTPException(status_code=500, detail="DATABASE_URL is not set.")

# Initialize the database connection pool
db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        try:
            # Create a connection pool with the specified database URL
            db_pool = await asyncpg.create_pool(
                DATABASE_URL, 
                ssl='require', 
                timeout=30, 
                min_size=5,  # Minimum number of connections
                max_size=20  # Maximum number of connections
            )
            logging.debug("Database pool initialized")
        except Exception as e:
            logging.error(f"Error initializing database pool: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize database connection pool.")

# Dependency for getting a database connection from the pool
async def get_db_connection():
    if db_pool is None:
        await init_db_pool()  # Ensure the pool is initialized
    try:
        # Acquire a connection from the pool
        async with db_pool.acquire() as conn:
            yield conn  # Return the connection for database operations
    except Exception as e:
        logging.error(f"Error acquiring database connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to acquire database connection.")

