from .settings import DatabaseSettings
from .pool import init_pool, get_pool
import asyncpg
from typing import Any, Optional

class DatabaseClient:
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self._pool = await init_pool(self.settings)

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        pool = self._pool or await get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        pool = self._pool or await get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> str:
        pool = self._pool or await get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
