"""
Claims Policy Search Service - Semantic search over automotive claims policy chunks.

Provides vector similarity search with filtering and hybrid search support for
the Ask IQ chat feature in the automotive claims persona.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.config import Settings, RAGSettings
from app.database.pool import get_pool
from app.rag.embeddings import EmbeddingService
from app.utils import setup_logging

logger = setup_logging()


@dataclass
class ClaimsSearchResult:
    """Represents a claims policy search result with relevance score."""

    chunk_id: str
    policy_id: str
    policy_name: str
    chunk_type: str
    category: str
    subcategory: str | None
    criteria_id: str | None
    severity: str | None
    risk_level: str | None
    liability_determination: str | None
    action_recommendation: str | None
    content: str
    similarity: float
    metadata: dict[str, Any]


class ClaimsPolicySearchService:
    """
    Semantic search service for automotive claims policy chunks.

    Supports:
    - Vector similarity search (cosine distance)
    - Filtered search by category/subcategory/severity
    - Similarity threshold filtering
    - Hybrid search (vector + text)
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
        self.table = f"{schema}.claim_policy_chunks"

        self.embedding_service = EmbeddingService(
            settings.openai,
            settings.rag,
        )

    async def semantic_search(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[ClaimsSearchResult]:
        """
        Basic vector similarity search.

        Args:
            query: Natural language query
            top_k: Number of results (default from settings)
            similarity_threshold: Minimum similarity (default from settings)

        Returns:
            List of ClaimsSearchResult objects ordered by similarity
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold

        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)

        pool = await get_pool()

        # Vector similarity search using cosine distance
        query_sql = f"""
            SELECT 
                id,
                policy_id,
                policy_name,
                chunk_type,
                category,
                subcategory,
                criteria_id,
                severity,
                risk_level,
                liability_determination,
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
                query_embedding,
                similarity_threshold,
                top_k,
            )

        results = [self._row_to_result(row) for row in rows]
        logger.debug(f"Claims search '{query[:50]}...' returned {len(results)} results")

        return results

    async def filtered_search(
        self,
        query: str,
        category: str | None = None,
        subcategory: str | None = None,
        severity: str | None = None,
        risk_level: str | None = None,
        chunk_types: list[str] | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[ClaimsSearchResult]:
        """
        Vector search with metadata filters.

        Args:
            query: Natural language query
            category: Filter by category (e.g., 'damage_assessment', 'liability')
            subcategory: Filter by subcategory
            severity: Filter by severity level
            risk_level: Filter by fraud risk level
            chunk_types: Filter by chunk types
            top_k: Number of results
            similarity_threshold: Minimum similarity

        Returns:
            Filtered list of ClaimsSearchResult objects
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold

        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)

        # Build WHERE clause
        conditions = ["1 - (embedding <=> $1::vector) >= $2"]
        params: list[Any] = [query_embedding, similarity_threshold]
        param_idx = 3

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1

        if subcategory:
            conditions.append(f"subcategory = ${param_idx}")
            params.append(subcategory)
            param_idx += 1

        if severity:
            conditions.append(f"severity = ${param_idx}")
            params.append(severity)
            param_idx += 1

        if risk_level:
            conditions.append(f"risk_level = ${param_idx}")
            params.append(risk_level)
            param_idx += 1

        if chunk_types:
            conditions.append(f"chunk_type = ANY(${param_idx})")
            params.append(chunk_types)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        params.append(top_k)

        query_sql = f"""
            SELECT 
                id,
                policy_id,
                policy_name,
                chunk_type,
                category,
                subcategory,
                criteria_id,
                severity,
                risk_level,
                liability_determination,
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

        results = [self._row_to_result(row) for row in rows]
        logger.debug(
            f"Filtered claims search '{query[:50]}...' "
            f"(category={category}) returned {len(results)} results"
        )

        return results

    async def hybrid_search(
        self,
        query: str,
        category: str | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        keyword_boost: float = 0.3,
    ) -> list[ClaimsSearchResult]:
        """
        Hybrid search combining vector similarity and keyword matching.

        The final score is: vector_similarity * (1 - keyword_boost) + keyword_score * keyword_boost

        Args:
            query: Natural language query
            category: Optional category filter
            top_k: Number of results
            similarity_threshold: Minimum similarity
            keyword_boost: Weight for keyword matching (0-1)

        Returns:
            List of ClaimsSearchResult objects with combined scoring
        """
        top_k = top_k or self.rag_settings.top_k
        similarity_threshold = similarity_threshold or self.rag_settings.similarity_threshold

        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding(query)

        # Build conditions
        conditions = ["1 - (embedding <=> $1::vector) >= $2"]
        params: list[Any] = [query_embedding, similarity_threshold, query]
        param_idx = 4

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        params.append(keyword_boost)
        params.append(top_k)

        # Hybrid scoring using ts_rank for keyword matching
        query_sql = f"""
            WITH vector_results AS (
                SELECT 
                    id,
                    policy_id,
                    policy_name,
                    chunk_type,
                    category,
                    subcategory,
                    criteria_id,
                    severity,
                    risk_level,
                    liability_determination,
                    action_recommendation,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) as vector_similarity,
                    ts_rank(
                        to_tsvector('english', content),
                        plainto_tsquery('english', $3)
                    ) as keyword_score
                FROM {self.table}
                WHERE {where_clause}
            )
            SELECT 
                *,
                (vector_similarity * (1 - ${param_idx}) + 
                 COALESCE(keyword_score, 0) * ${param_idx}) as similarity
            FROM vector_results
            ORDER BY similarity DESC
            LIMIT ${param_idx + 1}
        """

        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query_sql, *params)

        results = [self._row_to_result(row) for row in rows]
        logger.debug(
            f"Hybrid claims search '{query[:50]}...' returned {len(results)} results"
        )

        return results

    async def search_by_policy_category(
        self,
        query: str,
        category: str,
        top_k: int = 5,
    ) -> list[ClaimsSearchResult]:
        """
        Convenience method for searching within a specific policy category.

        Args:
            query: Natural language query
            category: One of: damage_assessment, liability, fraud_detection, payout_calculation
            top_k: Number of results

        Returns:
            List of ClaimsSearchResult objects
        """
        return await self.filtered_search(
            query=query,
            category=category,
            top_k=top_k,
        )

    async def get_relevant_policies_for_claim(
        self,
        damage_description: str | None = None,
        incident_description: str | None = None,
        estimate_amount: float | None = None,
        top_k: int = 10,
    ) -> dict[str, list[ClaimsSearchResult]]:
        """
        Get relevant policies across all categories for a claim.

        Args:
            damage_description: Description of vehicle damage
            incident_description: Description of the incident
            estimate_amount: Repair estimate amount
            top_k: Results per category

        Returns:
            Dict mapping category to search results
        """
        results: dict[str, list[ClaimsSearchResult]] = {}

        # Search damage policies if damage description provided
        if damage_description:
            results["damage_assessment"] = await self.search_by_policy_category(
                query=damage_description,
                category="damage_assessment",
                top_k=top_k,
            )

        # Search liability policies if incident description provided
        if incident_description:
            results["liability"] = await self.search_by_policy_category(
                query=incident_description,
                category="liability",
                top_k=top_k,
            )

        # Search fraud policies if relevant indicators
        if damage_description or incident_description:
            fraud_query = f"{damage_description or ''} {incident_description or ''}"
            results["fraud_detection"] = await self.search_by_policy_category(
                query=fraud_query.strip(),
                category="fraud_detection",
                top_k=top_k,
            )

        # Search payout policies if estimate provided
        if estimate_amount is not None:
            payout_query = f"repair estimate validation ${estimate_amount:.0f}"
            results["payout_calculation"] = await self.search_by_policy_category(
                query=payout_query,
                category="payout_calculation",
                top_k=top_k,
            )

        return results

    def _row_to_result(self, row) -> ClaimsSearchResult:
        """Convert database row to ClaimsSearchResult."""
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return ClaimsSearchResult(
            chunk_id=str(row["id"]),
            policy_id=row["policy_id"],
            policy_name=row["policy_name"],
            chunk_type=row["chunk_type"],
            category=row["category"],
            subcategory=row["subcategory"],
            criteria_id=row["criteria_id"],
            severity=row["severity"],
            risk_level=row["risk_level"],
            liability_determination=row["liability_determination"],
            action_recommendation=row["action_recommendation"],
            content=row["content"],
            similarity=float(row["similarity"]),
            metadata=metadata,
        )


async def get_claims_policy_context(
    settings: Settings,
    query: str,
    category: str | None = None,
    top_k: int = 5,
) -> str:
    """
    Convenience function to get claims policy context for RAG.

    Args:
        settings: Application settings
        query: User query
        category: Optional category filter
        top_k: Number of chunks to retrieve

    Returns:
        Formatted context string for LLM prompt
    """
    search_service = ClaimsPolicySearchService(settings)

    if category:
        results = await search_service.filtered_search(
            query=query,
            category=category,
            top_k=top_k,
        )
    else:
        results = await search_service.semantic_search(
            query=query,
            top_k=top_k,
        )

    if not results:
        return "No relevant claims policies found."

    context_parts = ["Relevant Automotive Claims Policies:\n"]
    for i, result in enumerate(results, 1):
        context_parts.append(f"[{i}] {result.policy_name} ({result.policy_id})")
        context_parts.append(f"    Category: {result.category}")
        if result.criteria_id:
            context_parts.append(f"    Criterion: {result.criteria_id}")
        context_parts.append(f"    Content: {result.content}")
        context_parts.append("")

    return "\n".join(context_parts)
