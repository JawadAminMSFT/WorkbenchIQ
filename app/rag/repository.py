"""
Policy Chunk Repository - CRUD operations for policy chunks in PostgreSQL.

Handles storage, retrieval, and updates of policy chunks with vector embeddings.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.database.pool import get_pool
from app.rag.chunker import PolicyChunk
from app.utils import setup_logging

logger = setup_logging()


class PolicyChunkRepository:
    """
    Repository for PolicyChunk entities in PostgreSQL.
    
    Provides:
    - Batch insert/upsert of chunks
    - Single chunk retrieval
    - Delete by policy ID
    - Hash-based change detection
    """
    
    def __init__(self, schema: str = "workbenchiq"):
        """
        Initialize repository.
        
        Args:
            schema: PostgreSQL schema name
        """
        self.schema = schema
        self.table = f"{schema}.policy_chunks"
    
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
            conflict_clause = """
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
        
        logger.info(f"Inserted/updated {inserted} chunks")
        return inserted
    
    async def get_chunk_by_id(self, chunk_id: UUID) -> PolicyChunk | None:
        """
        Retrieve a single chunk by ID.
        
        Args:
            chunk_id: UUID of the chunk
            
        Returns:
            PolicyChunk or None if not found
        """
        pool = await get_pool()
        
        query = f"""
            SELECT 
                id, policy_id, policy_version, policy_name,
                chunk_type, chunk_sequence, category, subcategory,
                criteria_id, risk_level, action_recommendation,
                content, content_hash, token_count,
                embedding, embedding_model, metadata
            FROM {self.table}
            WHERE id = $1
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, chunk_id)
        
        if not row:
            return None
        
        return self._row_to_chunk(row)
    
    async def delete_chunks_by_policy(self, policy_id: str) -> int:
        """
        Delete all chunks for a policy.
        
        Args:
            policy_id: Policy ID to delete chunks for
            
        Returns:
            Number of chunks deleted
        """
        pool = await get_pool()
        
        query = f"DELETE FROM {self.table} WHERE policy_id = $1"
        
        async with pool.acquire() as conn:
            result = await conn.execute(query, policy_id)
        
        # Parse 'DELETE N' result
        deleted = int(result.split()[-1]) if result else 0
        logger.info(f"Deleted {deleted} chunks for policy {policy_id}")
        return deleted
    
    async def get_all_chunk_hashes(self) -> dict[str, set[str]]:
        """
        Get all content hashes grouped by policy ID.
        
        Used for change detection during re-indexing.
        
        Returns:
            Dict mapping policy_id -> set of content hashes
        """
        pool = await get_pool()
        
        query = f"SELECT policy_id, content_hash FROM {self.table}"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        hashes: dict[str, set[str]] = {}
        for row in rows:
            policy_id = row["policy_id"]
            if policy_id not in hashes:
                hashes[policy_id] = set()
            hashes[policy_id].add(row["content_hash"])
        
        return hashes
    
    async def get_chunks_by_policy(self, policy_id: str) -> list[PolicyChunk]:
        """
        Get all chunks for a policy.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            List of PolicyChunk objects
        """
        pool = await get_pool()
        
        query = f"""
            SELECT 
                id, policy_id, policy_version, policy_name,
                chunk_type, chunk_sequence, category, subcategory,
                criteria_id, risk_level, action_recommendation,
                content, content_hash, token_count,
                embedding, embedding_model, metadata
            FROM {self.table}
            WHERE policy_id = $1
            ORDER BY chunk_sequence
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, policy_id)
        
        return [self._row_to_chunk(row) for row in rows]
    
    async def count_chunks(self, policy_id: str | None = None) -> int:
        """
        Count chunks, optionally filtered by policy.
        
        Args:
            policy_id: Optional policy ID filter
            
        Returns:
            Number of chunks
        """
        pool = await get_pool()
        
        if policy_id:
            query = f"SELECT COUNT(*) FROM {self.table} WHERE policy_id = $1"
            async with pool.acquire() as conn:
                return await conn.fetchval(query, policy_id)
        else:
            query = f"SELECT COUNT(*) FROM {self.table}"
            async with pool.acquire() as conn:
                return await conn.fetchval(query)
    
    def _row_to_chunk(self, row: Any) -> PolicyChunk:
        """Convert database row to PolicyChunk."""
        metadata = row.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        embedding = row.get("embedding")
        if isinstance(embedding, str):
            embedding = json.loads(embedding)
        
        return PolicyChunk(
            policy_id=row["policy_id"],
            policy_version=row["policy_version"],
            policy_name=row["policy_name"],
            chunk_type=row["chunk_type"],
            chunk_sequence=row["chunk_sequence"],
            category=row["category"],
            subcategory=row.get("subcategory"),
            criteria_id=row.get("criteria_id"),
            risk_level=row.get("risk_level"),
            action_recommendation=row.get("action_recommendation"),
            content=row["content"],
            content_hash=row["content_hash"],
            token_count=row["token_count"],
            embedding=embedding,
            metadata=metadata,
        )
