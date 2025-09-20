import asyncpg
from contextlib import asynccontextmanager
from .config import get_settings

settings = get_settings()

async def get_db_pool():
    return await asyncpg.create_pool(settings.database_url)

@asynccontextmanager
async def get_db_connection():
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection