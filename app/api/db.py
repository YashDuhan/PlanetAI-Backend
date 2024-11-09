import asyncpg
from fastapi import HTTPException
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Manually create a connection only for the upload endpoint
async def get_db_connection():
    try:
        # Manually create a new connection for each request
        conn = await asyncpg.connect(DATABASE_URL, ssl="require")
        return conn
    except Exception as e:
        logging.error(f"Error getting database connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database connection")

async def close_db_connection(conn):
    try:
        await conn.close()
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to close database connection")
