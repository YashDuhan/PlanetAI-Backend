import asyncpg
import os
from dotenv import load_dotenv
from fastapi import HTTPException

# Load env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise HTTPException(status_code=500, detail="DATABASE_URL is not set.")

# Initialize the database connection pool
db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, ssl='require', timeout=30)

# Dependency for getting a database connection from the pool
async def get_db_connection():
    if db_pool is None:
        await init_db_pool()
    async with db_pool.acquire() as conn:
        yield conn
