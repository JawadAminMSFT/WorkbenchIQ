"""Check existing indexes on policy_chunks table."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.pool import init_pool, close_pool
from app.database.settings import DatabaseSettings


async def main():
    db = DatabaseSettings.from_env()
    pool = await init_pool(db)
    
    async with pool.acquire() as conn:
        # Check diabetes policies
        print("Diabetes policies:")
        rows = await conn.fetch("""
            SELECT DISTINCT policy_id, category 
            FROM workbenchiq.policy_chunks 
            WHERE policy_id LIKE '%DM%'
        """)
        for r in rows:
            print(f"  {r['policy_id']}: {r['category']}")
        
        # Check all policy IDs
        print("\nAll policy IDs and categories:")
        rows = await conn.fetch("""
            SELECT DISTINCT policy_id, category 
            FROM workbenchiq.policy_chunks 
            ORDER BY category, policy_id
        """)
        for r in rows:
            print(f"  {r['policy_id']}: {r['category']}")
    
    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
