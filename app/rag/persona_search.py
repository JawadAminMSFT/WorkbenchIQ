"""
Persona-Aware Search Service Factory.

Provides a unified way to get the correct search service based on persona.
This allows Ask IQ to use the correct policy index for each persona type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.config import Settings
from app.rag.search import PolicySearchService, SearchResult
from app.rag.inference import CategoryInference, InferredContext
from app.utils import setup_logging

if TYPE_CHECKING:
    from app.claims.search import ClaimsPolicySearchService

logger = setup_logging()


# Mapping of personas to their search configurations
PERSONA_SEARCH_CONFIG = {
    "underwriting": {
        "table": "policy_chunks",
        "service_type": "underwriting",
        "description": "Life & health underwriting policies",
    },
    "life_health_claims": {
        "table": "health_claims_policy_chunks",
        "service_type": "health_claims",
        "description": "Life & health claims processing policies",
    },
    "automotive_claims": {
        "table": "claim_policy_chunks",
        "service_type": "automotive_claims",
        "description": "Automotive/auto claims processing policies",
    },
    "property_casualty_claims": {
        "table": "pc_claims_policy_chunks",
        "service_type": "pc_claims",
        "description": "Property & casualty claims policies",
    },
}


class HealthClaimsPolicySearchService(PolicySearchService):
    """
    Search service for life & health claims policies.
    
    Uses the health_claims_policy_chunks table for vector search.
    """
    
    def __init__(self, settings: Settings, schema: str = "workbenchiq"):
        super().__init__(settings, schema)
        # Override table to use health claims chunks
        self.table = f"{schema}.health_claims_policy_chunks"


class AutomotiveClaimsPolicySearchService(PolicySearchService):
    """
    Search service for automotive claims policies.
    
    Uses the claim_policy_chunks table for vector search.
    This uses the unified indexer schema (same as underwriting).
    """
    
    def __init__(self, settings: Settings, schema: str = "workbenchiq"):
        super().__init__(settings, schema)
        # Override table to use automotive claims chunks
        self.table = f"{schema}.claim_policy_chunks"


class PCClaimsPolicySearchService(PolicySearchService):
    """
    Search service for property & casualty claims policies.
    
    Uses the pc_claims_policy_chunks table for vector search.
    """
    
    def __init__(self, settings: Settings, schema: str = "workbenchiq"):
        super().__init__(settings, schema)
        # Override table to use P&C claims chunks
        self.table = f"{schema}.pc_claims_policy_chunks"


class ClaimsPolicySearchServiceAdapter:
    """
    Adapter for ClaimsPolicySearchService to make it compatible with RAGService.
    
    Wraps ClaimsPolicySearchService and adds the inference attribute and
    intelligent_search method that RAGService expects.
    """
    
    def __init__(self, claims_service, settings: Settings):
        self._claims_service = claims_service
        self.settings = settings
        self.rag_settings = settings.rag
        self.inference = CategoryInference(settings.openai)
        # Expose key attributes
        self.table = claims_service.table
        self.embedding_service = claims_service.embedding_service
    
    async def semantic_search(self, query: str, **kwargs) -> list[SearchResult]:
        """Delegate to claims service and convert results."""
        claims_results = await self._claims_service.semantic_search(query, **kwargs)
        return self._convert_results(claims_results)
    
    async def hybrid_search(self, query: str, **kwargs) -> list[SearchResult]:
        """Delegate to claims service and convert results."""
        claims_results = await self._claims_service.hybrid_search(query, **kwargs)
        return self._convert_results(claims_results)
    
    async def filtered_search(self, query: str, **kwargs) -> list[SearchResult]:
        """Delegate to claims service and convert results."""
        claims_results = await self._claims_service.filtered_search(query, **kwargs)
        return self._convert_results(claims_results)
    
    async def intelligent_search(
        self,
        query: str,
        use_llm_inference: bool = False,
        top_k: int | None = None,
    ) -> tuple[list[SearchResult], InferredContext | None]:
        """
        Intelligent search that combines category inference with semantic search.
        
        This is a simplified implementation for claims - it performs basic semantic
        search and returns inferred context.
        """
        # First, infer categories from the query
        inferred = await self.inference.infer_async(query, use_llm=use_llm_inference)
        
        # Perform semantic search
        results = await self.hybrid_search(query=query, top_k=top_k)
        
        return results, inferred
    
    def _convert_results(self, claims_results) -> list[SearchResult]:
        """Convert ClaimsSearchResult objects to SearchResult objects."""
        return [
            SearchResult(
                chunk_id=r.chunk_id,
                policy_id=r.policy_id,
                policy_name=r.policy_name,
                chunk_type=r.chunk_type,
                category=r.category,
                subcategory=r.subcategory,
                criteria_id=r.criteria_id,
                risk_level=r.risk_level,
                action_recommendation=r.action_recommendation,
                content=r.content,
                similarity=r.similarity,
                metadata=r.metadata,
            )
            for r in claims_results
        ]


def get_search_service_for_persona(
    persona: str,
    settings: Settings,
    schema: str = "workbenchiq",
) -> PolicySearchService:
    """
    Get the appropriate search service for a given persona.
    
    Args:
        persona: The persona type (underwriting, life_health_claims, automotive_claims, property_casualty_claims)
        settings: Application settings
        schema: PostgreSQL schema name
        
    Returns:
        The appropriate search service for the persona
        
    Raises:
        ValueError: If persona is not supported
    """
    if persona not in PERSONA_SEARCH_CONFIG:
        logger.warning(f"Unknown persona '{persona}', defaulting to underwriting")
        persona = "underwriting"
    
    config = PERSONA_SEARCH_CONFIG[persona]
    service_type = config["service_type"]
    
    logger.debug(f"Creating search service for persona '{persona}' using table '{config['table']}'")
    
    if service_type == "underwriting":
        return PolicySearchService(settings, schema)
    
    elif service_type == "health_claims":
        return HealthClaimsPolicySearchService(settings, schema)
    
    elif service_type == "automotive_claims":
        # Use the new unified-indexer-compatible search service
        return AutomotiveClaimsPolicySearchService(settings, schema)
    
    elif service_type == "pc_claims":
        return PCClaimsPolicySearchService(settings, schema)
    
    else:
        # Fallback to underwriting
        logger.warning(f"Unknown service type '{service_type}', defaulting to underwriting")
        return PolicySearchService(settings, schema)


def get_search_table_for_persona(persona: str, schema: str = "workbenchiq") -> str:
    """
    Get the database table name for a given persona's search index.
    
    Args:
        persona: The persona type
        schema: PostgreSQL schema name
        
    Returns:
        Full table name with schema (e.g., "workbenchiq.policy_chunks")
    """
    if persona not in PERSONA_SEARCH_CONFIG:
        logger.warning(f"Unknown persona '{persona}', defaulting to underwriting table")
        persona = "underwriting"
    
    table = PERSONA_SEARCH_CONFIG[persona]["table"]
    return f"{schema}.{table}"


def persona_supports_rag_search(persona: str) -> bool:
    """
    Check if a persona has RAG search support.
    
    Args:
        persona: The persona type
        
    Returns:
        True if persona has a configured search table
    """
    return persona in PERSONA_SEARCH_CONFIG
