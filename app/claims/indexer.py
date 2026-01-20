"""
Claims Policy Indexer - Orchestrates the indexing pipeline for automotive claims policies.

Pipeline: Load policies → Chunk → Embed → Store in PostgreSQL
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.claims.chunker import ClaimsPolicyChunk, ClaimsPolicyChunker
from app.claims.policies import ClaimsPolicyLoader
from app.config import Settings, load_settings
from app.database.pool import init_pool, get_pool
from app.rag.embeddings import EmbeddingService
from app.utils import setup_logging

logger = setup_logging()


class ClaimsIndexingError(Exception):
    """Raised when claims policy indexing fails."""
    pass


class ClaimsPolicyChunkRepository:
    """
    Repository for ClaimsPolicyChunk entities in PostgreSQL.

    Provides:
    - Batch insert/upsert of chunks
    - Delete by policy ID
    - Hash-based change detection
    """

    # SQL for creating the claims policy chunks table
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {schema}.claim_policy_chunks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        policy_id VARCHAR(50) NOT NULL,
        policy_version VARCHAR(20) NOT NULL,
        policy_name VARCHAR(255) NOT NULL,
        chunk_type VARCHAR(50) NOT NULL,
        chunk_sequence INT NOT NULL,
        category VARCHAR(100) NOT NULL,
        subcategory VARCHAR(100),
        criteria_id VARCHAR(50),
        severity VARCHAR(50),
        risk_level VARCHAR(50),
        liability_determination TEXT,
        action_recommendation TEXT,
        content TEXT NOT NULL,
        content_hash VARCHAR(64) NOT NULL,
        token_count INT NOT NULL,
        embedding vector(1536),
        embedding_model VARCHAR(100),
        metadata JSONB DEFAULT '{{}}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT claim_policy_chunks_unique 
            UNIQUE (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash)
    );

    -- Indexes for efficient searching
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_policy_id 
        ON {schema}.claim_policy_chunks(policy_id);
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_category 
        ON {schema}.claim_policy_chunks(category);
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_chunk_type 
        ON {schema}.claim_policy_chunks(chunk_type);
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_severity 
        ON {schema}.claim_policy_chunks(severity);
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_risk_level 
        ON {schema}.claim_policy_chunks(risk_level);

    -- Vector similarity index using IVFFlat
    CREATE INDEX IF NOT EXISTS idx_claim_policy_chunks_embedding 
        ON {schema}.claim_policy_chunks 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10);
    """

    def __init__(self, schema: str = "workbenchiq"):
        """
        Initialize repository.

        Args:
            schema: PostgreSQL schema name
        """
        self.schema = schema
        self.table = f"{schema}.claim_policy_chunks"

    async def initialize_table(self) -> None:
        """Create the claims policy chunks table if it doesn't exist."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(self.CREATE_TABLE_SQL.format(schema=self.schema))
            logger.info(f"Initialized {self.table} table")

    async def insert_chunks(
        self,
        chunks: list[ClaimsPolicyChunk],
        on_conflict: str = "update",
    ) -> int:
        """
        Insert or upsert claims policy chunks.

        Args:
            chunks: List of ClaimsPolicyChunk objects with embeddings
            on_conflict: 'update' to upsert, 'skip' to ignore duplicates

        Returns:
            Number of chunks inserted/updated
        """
        if not chunks:
            return 0

        pool = await get_pool()

        # Build conflict handling
        if on_conflict == "update":
            conflict_clause = """
                ON CONFLICT (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash)
                DO UPDATE SET
                    policy_name = EXCLUDED.policy_name,
                    policy_version = EXCLUDED.policy_version,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    severity = EXCLUDED.severity,
                    risk_level = EXCLUDED.risk_level,
                    liability_determination = EXCLUDED.liability_determination,
                    action_recommendation = EXCLUDED.action_recommendation,
                    content = EXCLUDED.content,
                    token_count = EXCLUDED.token_count,
                    embedding = EXCLUDED.embedding,
                    embedding_model = EXCLUDED.embedding_model,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """
        else:
            conflict_clause = "ON CONFLICT DO NOTHING"

        insert_query = f"""
            INSERT INTO {self.table} (
                policy_id, policy_version, policy_name,
                chunk_type, chunk_sequence, category, subcategory,
                criteria_id, severity, risk_level, liability_determination,
                action_recommendation, content, content_hash, token_count,
                embedding, embedding_model, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                $12, $13, $14, $15, $16, $17, $18
            )
            {conflict_clause}
        """

        inserted = 0
        async with pool.acquire() as conn:
            for chunk in chunks:
                if chunk.embedding is None:
                    logger.warning(
                        f"Skipping chunk without embedding: {chunk.policy_id}/{chunk.chunk_type}"
                    )
                    continue

                try:
                    result = await conn.execute(
                        insert_query,
                        chunk.policy_id,
                        chunk.policy_version,
                        chunk.policy_name,
                        chunk.chunk_type,
                        chunk.chunk_sequence,
                        chunk.category,
                        chunk.subcategory,
                        chunk.criteria_id,
                        chunk.severity,
                        chunk.risk_level,
                        chunk.liability_determination,
                        chunk.action_recommendation,
                        chunk.content,
                        chunk.content_hash,
                        chunk.token_count,
                        chunk.embedding,
                        "text-embedding-3-small",
                        json.dumps(chunk.metadata) if chunk.metadata else "{}",
                    )
                    if "INSERT" in result or "UPDATE" in result:
                        inserted += 1
                except Exception as e:
                    logger.error(
                        f"Failed to insert chunk {chunk.policy_id}/{chunk.criteria_id}: {e}"
                    )
                    raise

        logger.info(f"Inserted/updated {inserted} claims policy chunks")
        return inserted

    async def delete_chunks_by_policy(self, policy_id: str) -> int:
        """
        Delete all chunks for a specific policy.

        Args:
            policy_id: Policy ID to delete chunks for

        Returns:
            Number of chunks deleted
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table} WHERE policy_id = $1",
                policy_id,
            )
            # Extract count from 'DELETE N'
            count = int(result.split()[-1]) if result else 0
            return count

    async def delete_all_chunks(self) -> int:
        """
        Delete all claims policy chunks.

        Returns:
            Number of chunks deleted
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(f"DELETE FROM {self.table}")
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Deleted {count} claims policy chunks")
            return count

    async def get_chunk_count(self) -> int:
        """Get total number of chunks in the table."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.table}")
            return row[0] if row else 0


class ClaimsPolicyIndexer:
    """
    Orchestrates the claims policy indexing pipeline.

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
            policies_path: Path to claims policies JSON file
        """
        self.settings = settings or load_settings()
        self.policies_path = (
            Path(policies_path)
            if policies_path
            else Path("data/automotive-claims-policies.json")
        )

        # Initialize components
        self.policy_loader = ClaimsPolicyLoader()
        self.chunker = ClaimsPolicyChunker()
        self.embedding_service = EmbeddingService(
            self.settings.openai,
            self.settings.rag,
        )
        self.repository = ClaimsPolicyChunkRepository(
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
        Index all claims policies or specific policies.

        Args:
            policy_ids: Optional list of policy IDs to index (all if None)
            force_reindex: If True, delete existing chunks before indexing

        Returns:
            Metrics dict with counts and timing
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("Starting Claims Policy Indexing Pipeline")
        logger.info("=" * 60)

        # Ensure database connection and table
        await self._ensure_infrastructure()

        # Step 1: Load policies
        logger.info("\n📚 Step 1: Loading claims policies...")
        self.policy_loader.load_policies(self.policies_path)
        policies = self.policy_loader.get_all_policies()

        if policy_ids:
            policies = [p for p in policies if p.id in policy_ids]
            logger.info(f"   Filtered to {len(policies)} policies")

        if not policies:
            logger.warning("   No policies to index")
            return {"status": "skipped", "reason": "no policies"}

        logger.info(f"   Loaded {len(policies)} claims policies")

        # Step 2: Delete existing chunks if force reindex
        if force_reindex:
            logger.info("\n🗑️  Step 2: Clearing existing chunks...")
            for policy in policies:
                deleted = await self.repository.delete_chunks_by_policy(policy.id)
                if deleted:
                    logger.info(f"   Deleted {deleted} chunks for {policy.id}")

        # Step 3: Chunk policies
        logger.info("\n✂️  Step 3: Chunking policies...")
        all_chunks: list[ClaimsPolicyChunk] = []
        for policy in policies:
            chunks = self.chunker.chunk_policy(policy)
            all_chunks.extend(chunks)
            logger.info(f"   {policy.id}: {len(chunks)} chunks")

        logger.info(f"   Total chunks: {len(all_chunks)}")

        # Step 4: Generate embeddings
        logger.info("\n🧠 Step 4: Generating embeddings...")
        embed_start = time.time()
        self._embed_chunks(all_chunks, batch_size=50)
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
        logger.info("Claims Policy Indexing Complete")
        logger.info(f"  Policies: {len(policies)}")
        logger.info(f"  Chunks: {inserted}")
        logger.info(f"  Time: {total_time:.1f}s")
        logger.info("=" * 60)

        return self.metrics

    async def _ensure_infrastructure(self) -> None:
        """Ensure database pool and tables are ready."""
        try:
            await get_pool()
        except RuntimeError:
            await init_pool(self.settings.database)

        await self.repository.initialize_table()

    def _embed_chunks(
        self, chunks: list[ClaimsPolicyChunk], batch_size: int = 50
    ) -> None:
        """
        Generate embeddings for all chunks.

        Args:
            chunks: List of chunks to embed
            batch_size: Batch size for embedding API calls
        """
        # Extract texts from chunks
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings in batches
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.embedding_service.get_embeddings_batch(batch)
            all_embeddings.extend(embeddings)
            logger.debug(f"   Embedded batch {i // batch_size + 1}")

        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, all_embeddings):
            chunk.embedding = embedding
