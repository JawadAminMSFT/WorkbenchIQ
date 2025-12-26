"""
Policy Indexer - Orchestrates the full indexing pipeline.

Pipeline: Load policies → Chunk → Embed → Store in PostgreSQL
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.config import Settings, load_settings
from app.database.pool import init_pool, get_pool
from app.database.settings import DatabaseSettings
from app.rag.chunker import PolicyChunker, PolicyChunk
from app.rag.embeddings import EmbeddingService
from app.rag.repository import PolicyChunkRepository
from app.utils import setup_logging

logger = setup_logging()


class IndexingError(Exception):
    """Raised when indexing fails."""
    pass


class PolicyIndexer:
    """
    Orchestrates the policy indexing pipeline.
    
    Steps:
    1. Load policies from JSON file
    2. Chunk policies into searchable segments
    3. Generate embeddings for each chunk
    4. Store chunks in PostgreSQL with pgvector
    """
    
    def __init__(
        self,
        settings: Settings | None = None,
        policies_path: str | Path | None = None,
    ):
        """
        Initialize the indexer.
        
        Args:
            settings: Application settings (loads from env if not provided)
            policies_path: Path to policies JSON file
        """
        self.settings = settings or load_settings()
        self.policies_path = Path(policies_path) if policies_path else Path(
            "data/life-health-underwriting-policies.json"
        )
        
        # Initialize components
        self.chunker = PolicyChunker()
        self.embedding_service = EmbeddingService(
            self.settings.openai,
            self.settings.rag,
        )
        self.repository = PolicyChunkRepository(
            schema=self.settings.database.schema or "workbenchiq"
        )
        
        # Metrics
        self.metrics: dict[str, Any] = {}
    
    async def index_policies(
        self,
        policy_ids: list[str] | None = None,
        force_reindex: bool = False,
    ) -> dict[str, Any]:
        """
        Index all policies or specific policies.
        
        Args:
            policy_ids: Optional list of policy IDs to index (all if None)
            force_reindex: If True, delete existing chunks before indexing
            
        Returns:
            Metrics dict with counts and timing
        """
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("Starting Policy Indexing Pipeline")
        logger.info("=" * 60)
        
        # Ensure database connection
        await self._ensure_pool()
        
        # Step 1: Load policies
        logger.info("\n📚 Step 1: Loading policies...")
        policies = self._load_policies()
        
        if policy_ids:
            policies = [p for p in policies if p["id"] in policy_ids]
            logger.info(f"   Filtered to {len(policies)} policies")
        
        if not policies:
            logger.warning("   No policies to index")
            return {"status": "skipped", "reason": "no policies"}
        
        logger.info(f"   Loaded {len(policies)} policies")
        
        # Step 2: Delete existing chunks if force reindex
        if force_reindex:
            logger.info("\n🗑️  Step 2: Clearing existing chunks...")
            for policy in policies:
                deleted = await self.repository.delete_chunks_by_policy(policy["id"])
                if deleted:
                    logger.info(f"   Deleted {deleted} chunks for {policy['id']}")
        
        # Step 3: Chunk policies
        logger.info("\n✂️  Step 3: Chunking policies...")
        all_chunks: list[PolicyChunk] = []
        for policy in policies:
            chunks = self.chunker.chunk_policy(policy)
            all_chunks.extend(chunks)
            logger.info(f"   {policy['id']}: {len(chunks)} chunks")
        
        logger.info(f"   Total chunks: {len(all_chunks)}")
        
        # Step 4: Generate embeddings
        logger.info("\n🧠 Step 4: Generating embeddings...")
        embed_start = time.time()
        self.embedding_service.embed_chunks(all_chunks, batch_size=50)
        embed_time = time.time() - embed_start
        logger.info(f"   Embeddings generated in {embed_time:.1f}s")
        
        # Step 5: Store in database
        logger.info("\n💾 Step 5: Storing chunks in PostgreSQL...")
        store_start = time.time()
        inserted = await self.repository.insert_chunks(all_chunks)
        store_time = time.time() - store_start
        logger.info(f"   Stored {inserted} chunks in {store_time:.1f}s")
        
        # Summary
        total_time = time.time() - start_time
        
        self.metrics = {
            "status": "success",
            "policies_indexed": len(policies),
            "chunks_created": len(all_chunks),
            "chunks_stored": inserted,
            "embedding_time_seconds": round(embed_time, 2),
            "storage_time_seconds": round(store_time, 2),
            "total_time_seconds": round(total_time, 2),
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Indexing Complete!")
        logger.info(f"   Policies: {len(policies)}")
        logger.info(f"   Chunks: {inserted}")
        logger.info(f"   Time: {total_time:.1f}s")
        logger.info("=" * 60)
        
        return self.metrics
    
    async def reindex_policy(self, policy_id: str) -> dict[str, Any]:
        """
        Reindex a single policy.
        
        Deletes existing chunks and re-indexes from source.
        
        Args:
            policy_id: Policy ID to reindex
            
        Returns:
            Metrics dict
        """
        logger.info(f"Reindexing policy: {policy_id}")
        return await self.index_policies(
            policy_ids=[policy_id],
            force_reindex=True,
        )
    
    async def reindex_all(self) -> dict[str, Any]:
        """
        Reindex all policies.
        
        Clears all existing chunks and re-indexes from source.
        
        Returns:
            Metrics dict
        """
        logger.info("Reindexing all policies...")
        return await self.index_policies(force_reindex=True)
    
    def _load_policies(self) -> list[dict[str, Any]]:
        """Load policies from JSON file."""
        if not self.policies_path.exists():
            raise IndexingError(f"Policies file not found: {self.policies_path}")
        
        with open(self.policies_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        policies = data.get("policies", [])
        if not policies:
            logger.warning(f"No policies found in {self.policies_path}")
        
        return policies
    
    async def _ensure_pool(self):
        """Ensure database connection pool is initialized."""
        try:
            pool = await get_pool()
            if pool is None:
                raise Exception("Pool not initialized")
        except Exception:
            logger.info("Initializing database connection pool...")
            db_settings = DatabaseSettings.from_env()
            await init_pool(db_settings)
    
    async def get_index_stats(self) -> dict[str, Any]:
        """
        Get statistics about the current index.
        
        Returns:
            Dict with chunk counts, policy counts, etc.
        """
        # Ensure database connection
        await self._ensure_pool()
        
        total_chunks = await self.repository.count_chunks()
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Get distinct policies
            policy_count = await conn.fetchval(
                f"SELECT COUNT(DISTINCT policy_id) FROM {self.repository.table}"
            )
            
            # Get chunks by type
            type_counts = await conn.fetch(
                f"SELECT chunk_type, COUNT(*) as count FROM {self.repository.table} "
                f"GROUP BY chunk_type ORDER BY count DESC"
            )
            
            # Get chunks by category
            category_counts = await conn.fetch(
                f"SELECT category, COUNT(*) as count FROM {self.repository.table} "
                f"GROUP BY category ORDER BY count DESC"
            )
        
        return {
            "total_chunks": total_chunks,
            "policy_count": policy_count,
            "chunks_by_type": {row["chunk_type"]: row["count"] for row in type_counts},
            "chunks_by_category": {row["category"]: row["count"] for row in category_counts},
        }


# CLI entry point for manual indexing
async def main():
    """CLI entry point for manual policy indexing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index underwriting policies for RAG")
    parser.add_argument(
        "--policies",
        default="data/life-health-underwriting-policies.json",
        help="Path to policies JSON file",
    )
    parser.add_argument(
        "--policy-ids",
        nargs="*",
        help="Specific policy IDs to index (all if not specified)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reindex (delete existing chunks first)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics instead of indexing",
    )
    
    args = parser.parse_args()
    
    indexer = PolicyIndexer(policies_path=args.policies)
    
    if args.stats:
        stats = await indexer.get_index_stats()
        print("\n📊 Index Statistics:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Policies: {stats['policy_count']}")
        print(f"   By type: {stats['chunks_by_type']}")
        print(f"   By category: {stats['chunks_by_category']}")
    else:
        await indexer.index_policies(
            policy_ids=args.policy_ids,
            force_reindex=args.force,
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
