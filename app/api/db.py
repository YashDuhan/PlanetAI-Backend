import os
from asyncpg import create_pool, Connection
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Global DB pool variable
db_pool = None

async def init_db_pool():
    global db_pool
    # Parse the DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    result = urlparse(database_url)

    # Extract database details from the URL
    db_pool = await create_pool(
        user=result.username,
        password=result.password,
        database=result.path[1:],  # Remove the leading slash from the path
        host=result.hostname,
        port=result.port,
        ssl="require" in result.query  # Check for SSL mode in the query parameters
    )

async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()

def get_db_connection() -> Connection:
    if db_pool:
        return db_pool.acquire()
    raise Exception("DB pool is not initialized")
