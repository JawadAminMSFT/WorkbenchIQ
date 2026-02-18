import asyncpg
from typing import Optional
from .settings import DatabaseSettings

_pool: Optional[asyncpg.Pool] = None

async def init_pool(settings: DatabaseSettings) -> asyncpg.Pool:
    global _pool
    async def register_vector_codec(conn):
        try:
            await conn.set_type_codec(
                'vector',
                encoder=lambda v: '[' + ','.join(str(x) for x in v) + ']',
                decoder=lambda s: [float(x) for x in s.strip('[]').split(',')],
                schema='public',
                format='text',
            )
        except Exception:
            pass
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.host,
            port=settings.port,
            database=settings.database,
            user=settings.user,
            password=settings.password,
            ssl=settings.ssl_mode or "require",
            min_size=1,
            max_size=10,
            init=register_vector_codec,
        )
    return _pool

async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool

async def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
