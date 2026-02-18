"""
Policy Search Service - Semantic search over policy chunks.

Provides vector similarity search with filtering and hybrid search support.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.config import Settings, RAGSettings
from app.database.pool import get_pool
from app.rag.embeddings import EmbeddingService
from app.rag.inference import CategoryInference, InferredContext
from app.utils import setup_logging

logger = setup_logging()


@dataclass
class SearchResult:
    """Represents a search result with relevance score."""
    
    chunk_id: str
    policy_id: str
    policy_name: str
    chunk_type: str
    category: str
    subcategory: str | None
    criteria_id: str | None
    risk_level: str | None
    action_recommendation: str | None
    content: str
    similarity: float
    metadata: dict[str, Any]


class PolicySearchService:
    """
    Semantic search service for policy chunks.
    
    Supports:
    - Vector similarity search (cosine distance)
    - Filtered search by category/subcategory
    - Similarity threshold filtering
    - Hybrid search (vector + text)
    - Intelligent search with category inference
    """
    
    def __init__(
        self,
        settings: Settings,
        schema: str = "workbenchiq",
    ):
        """
        Initialize search service.
        
        Args:
            settings: Application settings
            schema: PostgreSQL schema name
        """
        self.settings = settings
        self.rag_settings = settings.rag
        self.schema = schema
        self.table = f"{schema}.policy_chunks"
        
        self.embedding_service = EmbeddingService(
            settings.openai,
            settings.rag,
        )
        
        self.inference = CategoryInference(settings.openai)
    
    async def semantic_search(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[SearchResult]:
        """
        Basic vector similarity search.
        
        Args:
            query: Natural language query
            top_k: Number of results (default from settings)
            similarity_threshold: Minimum similarity (default from settings)
            
        Returns:
            List of SearchResult objects ordered by similarity
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)
        
        pool = await get_pool()
        
        # Vector similarity search using cosine distance
        # Note: pgvector uses <=> for cosine distance (1 - similarity)
        # So we compute similarity as 1 - distance
        query_sql = f"""
            SELECT 
                id,
                policy_id,
                policy_name,
                chunk_type,
                category,
                subcategory,
                criteria_id,
                risk_level,
                action_recommendation,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM {self.table}
            WHERE 1 - (embedding <=> $1::vector) >= $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                query_sql,
                query_embedding,  # Pass list directly - codec handles conversion
                similarity_threshold,
                top_k,
            )
        
        results = [self._row_to_result(row) for row in rows]
        logger.debug(f"Search '{query[:50]}...' returned {len(results)} results")
        
        return results
    
    async def filtered_search(
        self,
        query: str,
        category: str | None = None,
        subcategory: str | None = None,
        risk_levels: list[str] | None = None,
        chunk_types: list[str] | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[SearchResult]:
        """
        Vector search with metadata filters.
        
        Args:
            query: Natural language query
            category: Filter by category (e.g., 'cardiovascular')
            subcategory: Filter by subcategory
            risk_levels: Filter by risk levels
            chunk_types: Filter by chunk types
            top_k: Number of results
            similarity_threshold: Minimum similarity
            
        Returns:
            Filtered list of SearchResult objects
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)
        
        # Build WHERE clause
        conditions = ["1 - (embedding <=> $1::vector) >= $2"]
        params: list[Any] = [query_embedding, similarity_threshold]  # Pass list directly
        param_idx = 3
        
        # Log active filters for debugging (T073)
        active_filters = []
        
        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1
            active_filters.append(f"category={category}")
        
        if subcategory:
            conditions.append(f"subcategory = ${param_idx}")
            params.append(subcategory)
            param_idx += 1
            active_filters.append(f"subcategory={subcategory}")
        
        if risk_levels:
            conditions.append(f"risk_level = ANY(${param_idx})")
            params.append(risk_levels)
            param_idx += 1
            active_filters.append(f"risk_levels={risk_levels}")
        
        if chunk_types:
            conditions.append(f"chunk_type = ANY(${param_idx})")
            params.append(chunk_types)
            param_idx += 1
            active_filters.append(f"chunk_types={chunk_types}")
        
        if active_filters:
            logger.debug(f"Filtered search active filters: {', '.join(active_filters)}")
        
        params.append(top_k)
        
        where_clause = " AND ".join(conditions)
        
        query_sql = f"""
            SELECT 
                id,
                policy_id,
                policy_name,
                chunk_type,
                category,
                subcategory,
                criteria_id,
                risk_level,
                action_recommendation,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM {self.table}
            WHERE {where_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT ${param_idx}
        """
        
        pool = await get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query_sql, *params)
        
        return [self._row_to_result(row) for row in rows]
    
    async def intelligent_search(
        self,
        query: str,
        use_llm_inference: bool = False,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> tuple[list[SearchResult], InferredContext]:
        """
        Intelligent search with automatic category inference.
        
        Uses keyword-based (and optionally LLM) inference to identify
        relevant categories, then performs filtered search.
        
        Args:
            query: Natural language query
            use_llm_inference: Whether to use LLM for better inference
            top_k: Number of results
            similarity_threshold: Minimum similarity
            
        Returns:
            Tuple of (search results, inferred context)
        """
        # Infer categories from query
        inferred = await self.inference.infer_async(
            query,
            use_llm=use_llm_inference,
        )
        
        logger.info(
            f"Intelligent search: inferred categories={inferred.categories}, "
            f"confidence={inferred.confidence:.2f}"
        )
        
        # If we have inferred filters with reasonable confidence, use them
        if inferred.has_filters() and inferred.confidence >= 0.3:
            # Use first category (most relevant based on match count)
            category = inferred.categories[0] if inferred.categories else None
            subcategory = inferred.subcategories[0] if inferred.subcategories else None
            risk_levels = inferred.risk_levels if inferred.risk_levels else None
            
            results = await self.filtered_search(
                query=query,
                category=category,
                subcategory=subcategory,
                risk_levels=risk_levels,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )
            
            # If filtered search returns few results, supplement with unfiltered
            if len(results) < (top_k or self.rag_settings.top_k) // 2:
                logger.debug("Filtered search returned few results, supplementing with unfiltered")
                unfiltered = await self.semantic_search(
                    query=query,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                )
                # Deduplicate by chunk_id
                seen_ids = {r.chunk_id for r in results}
                for r in unfiltered:
                    if r.chunk_id not in seen_ids:
                        results.append(r)
                        seen_ids.add(r.chunk_id)
                # Re-sort by similarity
                results.sort(key=lambda x: x.similarity, reverse=True)
                # Limit to top_k
                results = results[: (top_k or self.rag_settings.top_k)]
        else:
            # No strong inference, use pure semantic search
            results = await self.semantic_search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )
        
        return results, inferred

    async def hybrid_search(
        self,
        query: str,
        text_weight: float = 0.3,
        vector_weight: float = 0.7,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[SearchResult]:
        """
        Hybrid search combining vector similarity and text matching.
        
        Uses pg_trgm for text similarity combined with pgvector.
        
        Args:
            query: Natural language query
            text_weight: Weight for text similarity (0-1)
            vector_weight: Weight for vector similarity (0-1)
            top_k: Number of results
            similarity_threshold: Minimum combined score
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)
        
        pool = await get_pool()
        
        # Check if pg_trgm is available
        async with pool.acquire() as conn:
            trgm_check = await conn.fetchval(
                "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'"
            )
        
        if not trgm_check:
            logger.warning("pg_trgm not available, falling back to vector-only search")
            return await self.semantic_search(query, top_k, similarity_threshold)
        
        # Hybrid search combining vector and trigram similarity
        # Uses MAX of individual scores boosted, not weighted average
        # This prevents low trigram scores from dragging down good semantic matches
        # Also includes exact policy_id matching for ID lookups
        query_sql = f"""
            SELECT 
                id,
                policy_id,
                policy_name,
                chunk_type,
                category,
                subcategory,
                criteria_id,
                risk_level,
                action_recommendation,
                content,
                metadata,
                GREATEST(
                    -- Semantic similarity (primary)
                    (1 - (embedding <=> $1::vector)),
                    -- Trigram boosted (for keyword matches)
                    $4 * (1 - (embedding <=> $1::vector)) + $3 * COALESCE(similarity(content, $2), 0),
                    -- Policy ID exact match boost
                    CASE WHEN UPPER(policy_id) = UPPER($2) THEN 0.95 ELSE 0 END
                ) as similarity
            FROM {self.table}
            WHERE 
                -- Match if semantic is good enough
                (1 - (embedding <=> $1::vector)) >= $5
                -- OR trigram match is significant
                OR similarity(content, $2) > 0.1
                -- OR exact policy_id match
                OR UPPER(policy_id) = UPPER($2)
            ORDER BY GREATEST(
                (1 - (embedding <=> $1::vector)),
                $4 * (1 - (embedding <=> $1::vector)) + $3 * COALESCE(similarity(content, $2), 0),
                CASE WHEN UPPER(policy_id) = UPPER($2) THEN 0.95 ELSE 0 END
            ) DESC
            LIMIT $6
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                query_sql,
                query_embedding,  # Pass list directly - codec handles conversion
                query,
                vector_weight,
                text_weight,
                similarity_threshold,
                top_k,
            )
        
        return [self._row_to_result(row) for row in rows]
    
    async def search_by_policy(
        self,
        policy_id: str,
        query: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """
        Search within a specific policy.
        
        Args:
            policy_id: Policy ID to search within
            query: Optional query (returns all chunks if None)
            top_k: Number of results
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or self.rag_settings.top_k
        
        pool = await get_pool()
        
        if query:
            # Vector search within policy
            query_embedding = self.embedding_service.get_embedding(query)
            
            query_sql = f"""
                SELECT 
                    id,
                    policy_id,
                    policy_name,
                    chunk_type,
                    category,
                    subcategory,
                    criteria_id,
                    risk_level,
                    action_recommendation,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {self.table}
                WHERE policy_id = $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
            """
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    query_sql,
                    query_embedding,  # Pass list directly - codec handles conversion
                    policy_id,
                    top_k,
                )
        else:
            # Return all chunks for policy
            query_sql = f"""
                SELECT 
                    id,
                    policy_id,
                    policy_name,
                    chunk_type,
                    category,
                    subcategory,
                    criteria_id,
                    risk_level,
                    action_recommendation,
                    content,
                    metadata,
                    1.0 as similarity
                FROM {self.table}
                WHERE policy_id = $1
                ORDER BY chunk_sequence
                LIMIT $2
            """
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query_sql, policy_id, top_k)
        
        return [self._row_to_result(row) for row in rows]
    
    def _row_to_result(self, row: Any) -> SearchResult:
        """Convert database row to SearchResult."""
        metadata = row.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        return SearchResult(
            chunk_id=str(row["id"]),
            policy_id=row["policy_id"],
            policy_name=row["policy_name"],
            chunk_type=row["chunk_type"],
            category=row["category"],
            subcategory=row.get("subcategory"),
            criteria_id=row.get("criteria_id"),
            risk_level=row.get("risk_level"),
            action_recommendation=row.get("action_recommendation"),
            content=row["content"],
            similarity=float(row.get("similarity", 0)),
            metadata=metadata,
        )
