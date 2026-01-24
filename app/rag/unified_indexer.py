"""
Unified Policy Indexer - A single parameterized indexer for all personas.

This replaces the separate persona-specific indexers with one unified implementation
that uses the same schema and logic as the working underwriting indexer.

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
from app.utils import setup_logging

logger = setup_logging()


class IndexingError(Exception):
    """Raised when indexing fails."""
    pass


# Persona configuration mapping
PERSONA_CONFIG = {
    "underwriting": {
        "policies_path": "data/life-health-underwriting-policies.json",
        "table_name": "policy_chunks",
        "display_name": "Underwriting",
    },
    "life_health_claims": {
        "policies_path": "data/life-health-claims-policies.json",
        "table_name": "health_claims_policy_chunks",
        "display_name": "Life & Health Claims",
    },
    "automotive_claims": {
        "policies_path": "data/automotive-claims-policies.json",
        "table_name": "claim_policy_chunks",
        "display_name": "Automotive Claims",
    },
    "property_casualty_claims": {
        "policies_path": "data/property-casualty-claims-policies.json",
        "table_name": "pc_claims_policy_chunks",
        "display_name": "Property & Casualty Claims",
    },
}


class UnifiedPolicyChunkRepository:
    """
    Repository for PolicyChunk entities in PostgreSQL.
    
    Parameterized by table name to support all personas with the same schema.
    Uses the same proven structure as the underwriting policy_chunks table.
    """
    
    # SQL template for creating persona-specific tables
    # Uses CREATE UNIQUE INDEX for COALESCE expressions (not inline CONSTRAINT)
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {schema}.{table} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        policy_id VARCHAR(50) NOT NULL,
        policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
        policy_name VARCHAR(200) NOT NULL,
        chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
            'policy_header',
            'criteria',
            'modifying_factor',
            'reference',
            'description'
        )),
        chunk_sequence INTEGER NOT NULL DEFAULT 0,
        category VARCHAR(50) NOT NULL,
        subcategory VARCHAR(50),
        criteria_id VARCHAR(50),
        risk_level VARCHAR(30),
        action_recommendation TEXT,
        content TEXT NOT NULL,
        content_hash VARCHAR(64) NOT NULL,
        token_count INTEGER NOT NULL DEFAULT 0,
        embedding VECTOR(1536) NOT NULL,
        embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
        metadata JSONB DEFAULT '{{}}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Create unique index for upsert operations (must be index, not constraint, due to COALESCE)
    CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_unique ON {schema}.{table} 
        (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

    -- Create HNSW index for fast vector search
    CREATE INDEX IF NOT EXISTS idx_{table}_embedding ON {schema}.{table} 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);

    -- Additional indexes for filtering
    CREATE INDEX IF NOT EXISTS idx_{table}_category ON {schema}.{table} (category);
    CREATE INDEX IF NOT EXISTS idx_{table}_subcategory ON {schema}.{table} (subcategory);
    CREATE INDEX IF NOT EXISTS idx_{table}_policy_id ON {schema}.{table} (policy_id);
    CREATE INDEX IF NOT EXISTS idx_{table}_risk_level ON {schema}.{table} (risk_level);
    CREATE INDEX IF NOT EXISTS idx_{table}_chunk_type ON {schema}.{table} (chunk_type);
    CREATE INDEX IF NOT EXISTS idx_{table}_metadata ON {schema}.{table} USING gin (metadata);
    """

    def __init__(self, schema: str, table_name: str):
        """
        Initialize repository.
        
        Args:
            schema: PostgreSQL schema name
            table_name: Table name (without schema prefix)
        """
        self.schema = schema
        self.table_name = table_name
        self.table = f"{schema}.{table_name}"
    
    async def initialize_table(self) -> None:
        """Create the policy chunks table if it doesn't exist."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            sql = self.CREATE_TABLE_SQL.format(
                schema=self.schema,
                table=self.table_name,
            )
            await conn.execute(sql)
            logger.info(f"Initialized {self.table} table")
    
    async def insert_chunks(
        self,
        chunks: list[PolicyChunk],
        on_conflict: str = "update",
    ) -> int:
        """
        Insert or upsert policy chunks.
        
        Args:
            chunks: List of PolicyChunk objects with embeddings
            on_conflict: 'update' to upsert, 'skip' to ignore duplicates
            
        Returns:
            Number of chunks inserted/updated
        """
        if not chunks:
            return 0
        
        pool = await get_pool()
        
        # Build batch insert with ON CONFLICT handling
        if on_conflict == "update":
            conflict_clause = f"""
                ON CONFLICT (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash)
                DO UPDATE SET
                    policy_name = EXCLUDED.policy_name,
                    policy_version = EXCLUDED.policy_version,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    risk_level = EXCLUDED.risk_level,
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
                criteria_id, risk_level, action_recommendation,
                content, content_hash, token_count,
                embedding, embedding_model, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16
            )
            {conflict_clause}
        """
        
        inserted = 0
        async with pool.acquire() as conn:
            for chunk in chunks:
                if chunk.embedding is None:
                    logger.warning(f"Skipping chunk without embedding: {chunk.policy_id}/{chunk.chunk_type}")
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
                        chunk.risk_level,
                        chunk.action_recommendation,
                        chunk.content,
                        chunk.content_hash,
                        chunk.token_count,
                        chunk.embedding,  # Pass list directly - codec handles conversion
                        "text-embedding-3-small",
                        json.dumps(chunk.metadata) if chunk.metadata else "{}",
                    )
                    # asyncpg returns 'INSERT 0 1' or 'UPDATE 1'
                    if "INSERT" in result or "UPDATE" in result:
                        inserted += 1
                except Exception as e:
                    logger.error(f"Failed to insert chunk {chunk.policy_id}/{chunk.criteria_id}: {e}")
                    raise
        
        logger.info(f"Inserted/updated {inserted} chunks into {self.table}")
        return inserted
    
    async def delete_chunks_by_policy(self, policy_id: str) -> int:
        """Delete all chunks for a policy."""
        pool = await get_pool()
        query = f"DELETE FROM {self.table} WHERE policy_id = $1"
        async with pool.acquire() as conn:
            result = await conn.execute(query, policy_id)
        deleted = int(result.split()[-1]) if result else 0
        logger.info(f"Deleted {deleted} chunks for policy {policy_id}")
        return deleted
    
    async def delete_all_chunks(self) -> int:
        """Delete all chunks from the table."""
        pool = await get_pool()
        query = f"DELETE FROM {self.table}"
        async with pool.acquire() as conn:
            result = await conn.execute(query)
        deleted = int(result.split()[-1]) if result else 0
        logger.info(f"Deleted {deleted} chunks from {self.table}")
        return deleted
    
    async def count_chunks(self, policy_id: str | None = None) -> int:
        """Count chunks, optionally filtered by policy."""
        pool = await get_pool()
        if policy_id:
            query = f"SELECT COUNT(*) FROM {self.table} WHERE policy_id = $1"
            async with pool.acquire() as conn:
                return await conn.fetchval(query, policy_id)
        else:
            query = f"SELECT COUNT(*) FROM {self.table}"
            async with pool.acquire() as conn:
                return await conn.fetchval(query)


class UnifiedPolicyIndexer:
    """
    Unified policy indexer for all personas.
    
    Uses the same proven logic as the underwriting PolicyIndexer,
    but parameterized by persona to support all persona types.
    
    Steps:
    1. Load policies from persona-specific JSON file
    2. Chunk policies into searchable segments
    3. Generate embeddings for each chunk
    4. Store chunks in PostgreSQL with pgvector
    """
    
    def __init__(
        self,
        persona: str,
        settings: Settings | None = None,
        policies_path: str | Path | None = None,
    ):
        """
        Initialize the indexer.
        
        Args:
            persona: Persona ID (underwriting, life_health_claims, etc.)
            settings: Application settings (loads from env if not provided)
            policies_path: Override path to policies JSON file
        """
        self.persona = persona.lower()
        self.settings = settings or load_settings()
        
        # Get persona config
        config = PERSONA_CONFIG.get(self.persona)
        if not config:
            raise ValueError(
                f"Persona '{persona}' not supported. "
                f"Supported: {list(PERSONA_CONFIG.keys())}"
            )
        
        self.display_name = config["display_name"]
        self.policies_path = Path(policies_path) if policies_path else Path(config["policies_path"])
        
        # Initialize components
        self.chunker = PolicyChunker()
        self.embedding_service = EmbeddingService(
            self.settings.openai,
            self.settings.rag,
        )
        
        schema = self.settings.database.schema or "workbenchiq"
        self.repository = UnifiedPolicyChunkRepository(
            schema=schema,
            table_name=config["table_name"],
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
        logger.info(f"Starting {self.display_name} Policy Indexing Pipeline")
        logger.info("=" * 60)
        
        # Ensure database connection
        await self._ensure_pool()
        
        # Initialize table (create if not exists)
        logger.info("\n📋 Initializing database table...")
        await self.repository.initialize_table()
        
        # Step 1: Load policies
        logger.info("\n📚 Step 1: Loading policies...")
        policies = self._load_policies()
        
        if policy_ids:
            policies = [p for p in policies if p["id"] in policy_ids]
            logger.info(f"   Filtered to {len(policies)} policies")
        
        if not policies:
            logger.warning("   No policies to index")
            return {"status": "skipped", "reason": "no policies", "persona": self.persona}
        
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
            "persona": self.persona,
            "policies_indexed": len(policies),
            "chunks_created": len(all_chunks),
            "chunks_stored": inserted,
            "embedding_time_seconds": round(embed_time, 2),
            "storage_time_seconds": round(store_time, 2),
            "total_time_seconds": round(total_time, 2),
        }
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ {self.display_name} Indexing Complete!")
        logger.info(f"   Policies: {len(policies)}")
        logger.info(f"   Chunks: {inserted}")
        logger.info(f"   Time: {total_time:.1f}s")
        logger.info("=" * 60)
        
        return self.metrics
    
    async def reindex_policy(self, policy_id: str) -> dict[str, Any]:
        """Reindex a single policy."""
        logger.info(f"Reindexing policy: {policy_id}")
        return await self.index_policies(
            policy_ids=[policy_id],
            force_reindex=True,
        )
    
    async def reindex_all(self) -> dict[str, Any]:
        """Reindex all policies."""
        logger.info(f"Reindexing all {self.display_name} policies...")
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
        """Get statistics about the current index."""
        await self._ensure_pool()
        
        total_chunks = await self.repository.count_chunks()
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Check if table exists first
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = $1 AND table_name = $2
                )
                """,
                self.repository.schema,
                self.repository.table_name,
            )
            
            if not table_exists:
                return {
                    "persona": self.persona,
                    "total_chunks": 0,
                    "policy_count": 0,
                    "table": self.repository.table,
                    "message": "Table not yet created. Run reindex to initialize.",
                }
            
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
            "persona": self.persona,
            "total_chunks": total_chunks,
            "policy_count": policy_count,
            "chunks_by_type": {row["chunk_type"]: row["count"] for row in type_counts},
            "chunks_by_category": {row["category"]: row["count"] for row in category_counts},
            "table": self.repository.table,
        }


def get_supported_personas() -> list[str]:
    """Return list of personas that support RAG policy indexing."""
    return list(PERSONA_CONFIG.keys())


def persona_supports_rag(persona: str) -> bool:
    """Check if a persona supports RAG policy indexing."""
    return persona.lower() in PERSONA_CONFIG


async def get_indexer_for_persona(
    persona: str,
    settings: Settings | None = None,
) -> UnifiedPolicyIndexer:
    """
    Get the unified policy indexer for a persona.
    
    Args:
        persona: Persona ID (underwriting, life_health_claims, automotive_claims, etc.)
        settings: Optional application settings
        
    Returns:
        UnifiedPolicyIndexer instance for the specified persona
        
    Raises:
        ValueError: If persona is not supported for RAG indexing
    """
    if not persona_supports_rag(persona):
        raise ValueError(
            f"Persona '{persona}' does not support RAG policy indexing. "
            f"Supported personas: {get_supported_personas()}"
        )
    
    return UnifiedPolicyIndexer(persona=persona, settings=settings)


async def get_index_stats_for_persona(
    persona: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Get index statistics for a persona's policy table.
    
    Args:
        persona: Persona ID
        settings: Optional application settings
        
    Returns:
        Dict with status, chunk_count, policy_count, etc.
    """
    try:
        indexer = await get_indexer_for_persona(persona, settings)
        return await indexer.get_index_stats()
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Failed to get index stats for {persona}: {e}")
        return {"status": "error", "error": str(e)}


# CLI entry point
async def main():
    """CLI entry point for unified policy indexing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified policy indexer for all personas")
    parser.add_argument(
        "--persona",
        required=True,
        choices=get_supported_personas(),
        help="Persona to index policies for",
    )
    parser.add_argument(
        "--policies",
        default=None,
        help="Override path to policies JSON file",
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
    
    indexer = UnifiedPolicyIndexer(
        persona=args.persona,
        policies_path=args.policies,
    )
    
    if args.stats:
        stats = await indexer.get_index_stats()
        print(f"\n📊 {indexer.display_name} Index Statistics:")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Policies: {stats.get('policy_count', 0)}")
        print(f"   Table: {stats.get('table', 'N/A')}")
        if stats.get('chunks_by_type'):
            print(f"   By type: {stats['chunks_by_type']}")
        if stats.get('chunks_by_category'):
            print(f"   By category: {stats['chunks_by_category']}")
    else:
        await indexer.index_policies(
            policy_ids=args.policy_ids,
            force_reindex=args.force,
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
