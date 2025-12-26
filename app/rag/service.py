"""
RAG Service - Unified interface for RAG-enhanced chat.

Provides a single entry point for:
- Query understanding with category inference
- Semantic/hybrid search over policy chunks
- Context assembly for LLM prompts
- Fallback to full policy injection if RAG fails
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.config import Settings, load_settings
from app.database.pool import init_pool, get_pool
from app.database.settings import DatabaseSettings
from app.rag.context import RAGContextBuilder, RAGContext
from app.rag.search import PolicySearchService, SearchResult
from app.rag.inference import InferredContext
from app.utils import setup_logging

if TYPE_CHECKING:
    pass

logger = setup_logging()


@dataclass
class RAGQueryResult:
    """Result from a RAG query operation."""
    
    # The assembled context for the LLM prompt
    context: str
    
    # Structured context object with citations
    rag_context: RAGContext | None = None
    
    # Inferred categories/context from query
    inferred: InferredContext | None = None
    
    # Search results used
    results: list[SearchResult] = field(default_factory=list)
    
    # Metrics
    search_latency_ms: float = 0.0
    assembly_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    chunks_retrieved: int = 0
    tokens_used: int = 0
    
    # Whether fallback was used
    used_fallback: bool = False
    fallback_reason: str | None = None


class RAGService:
    """
    Unified RAG service for chat integration.
    
    Orchestrates:
    1. Category inference from user query
    2. Semantic/hybrid search for relevant policy chunks
    3. Context assembly with token budgets
    4. Fallback handling when RAG is unavailable
    """
    
    def __init__(
        self,
        settings: Settings | None = None,
        max_context_tokens: int = 4000,
        use_hybrid_search: bool = True,
    ):
        """
        Initialize RAG service.
        
        Args:
            settings: Application settings
            max_context_tokens: Maximum tokens for assembled context
            use_hybrid_search: Whether to use hybrid (keyword+semantic) search
        """
        self.settings = settings or load_settings()
        self.max_context_tokens = max_context_tokens
        self.use_hybrid_search = use_hybrid_search
        
        # Lazy initialization of components
        self._search_service: PolicySearchService | None = None
        self._context_builder: RAGContextBuilder | None = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection and services."""
        if self._initialized:
            return
        
        try:
            # Initialize database pool
            db_settings = DatabaseSettings.from_env()
            await init_pool(db_settings)
            
            # Initialize search service
            self._search_service = PolicySearchService(self.settings)
            
            # Initialize context builder
            self._context_builder = RAGContextBuilder(
                max_tokens=self.max_context_tokens,
            )
            
            self._initialized = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    @property
    def search_service(self) -> PolicySearchService:
        """Get search service (initializes if needed)."""
        if not self._search_service:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")
        return self._search_service
    
    @property
    def context_builder(self) -> RAGContextBuilder:
        """Get context builder."""
        if not self._context_builder:
            self._context_builder = RAGContextBuilder(max_tokens=self.max_context_tokens)
        return self._context_builder
    
    async def query(
        self,
        user_query: str,
        use_llm_inference: bool = False,
        top_k: int | None = None,
        include_citations: bool = True,
    ) -> RAGQueryResult:
        """
        Execute full RAG pipeline for a user query.
        
        Args:
            user_query: The user's question or message
            use_llm_inference: Whether to use LLM for category inference
            top_k: Number of chunks to retrieve
            include_citations: Whether to include citations in context
            
        Returns:
            RAGQueryResult with context and metrics
        """
        start_time = time.time()
        
        try:
            # Ensure initialized
            await self.initialize()
            
            # Step 1: Search with category inference
            search_start = time.time()
            
            if self.use_hybrid_search:
                # Try hybrid search first
                results = await self.search_service.hybrid_search(
                    query=user_query,
                    top_k=top_k or self.settings.rag.top_k,
                )
                
                # If hybrid returns nothing, fall back to intelligent search
                if not results:
                    results, inferred = await self.search_service.intelligent_search(
                        query=user_query,
                        use_llm_inference=use_llm_inference,
                        top_k=top_k,
                    )
                else:
                    # Still do inference for metadata
                    inferred = await self.search_service.inference.infer_async(
                        user_query,
                        use_llm=use_llm_inference,
                    )
            else:
                # Use intelligent search (semantic + category filter)
                results, inferred = await self.search_service.intelligent_search(
                    query=user_query,
                    use_llm_inference=use_llm_inference,
                    top_k=top_k,
                )
            
            search_latency = (time.time() - search_start) * 1000
            
            # Step 2: Assemble context
            assembly_start = time.time()
            
            rag_context = self.context_builder.assemble_context(
                results=results,
                query=user_query,
                format_style="structured",
            )
            
            assembly_latency = (time.time() - assembly_start) * 1000
            total_latency = (time.time() - start_time) * 1000
            
            # Log metrics
            logger.info(
                f"RAG query completed: {len(results)} chunks, "
                f"{rag_context.total_tokens} tokens, "
                f"{total_latency:.0f}ms total"
            )
            
            return RAGQueryResult(
                context=rag_context.context_text,
                rag_context=rag_context,
                inferred=inferred,
                results=results,
                search_latency_ms=search_latency,
                assembly_latency_ms=assembly_latency,
                total_latency_ms=total_latency,
                chunks_retrieved=len(results),
                tokens_used=rag_context.total_tokens,
                used_fallback=False,
            )
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            
            # Return empty result with error info
            total_latency = (time.time() - start_time) * 1000
            
            return RAGQueryResult(
                context="",
                used_fallback=True,
                fallback_reason=str(e),
                total_latency_ms=total_latency,
            )
    
    async def query_with_fallback(
        self,
        user_query: str,
        fallback_context: str,
        use_llm_inference: bool = False,
        top_k: int | None = None,
    ) -> RAGQueryResult:
        """
        Execute RAG query with automatic fallback to full policies.
        
        Args:
            user_query: The user's question
            fallback_context: Full policy context to use if RAG fails
            use_llm_inference: Whether to use LLM inference
            top_k: Number of chunks
            
        Returns:
            RAGQueryResult - either RAG context or fallback
        """
        result = await self.query(
            user_query=user_query,
            use_llm_inference=use_llm_inference,
            top_k=top_k,
        )
        
        # Use fallback if RAG failed or returned no results
        if result.used_fallback or result.chunks_retrieved == 0:
            logger.warning(
                f"Using fallback context. Reason: {result.fallback_reason or 'no chunks retrieved'}"
            )
            return RAGQueryResult(
                context=fallback_context,
                used_fallback=True,
                fallback_reason=result.fallback_reason or "no chunks retrieved",
                total_latency_ms=result.total_latency_ms,
            )
        
        return result
    
    def format_context_for_prompt(
        self,
        result: RAGQueryResult,
        include_header: bool = True,
    ) -> str:
        """
        Format RAG context for inclusion in system prompt.
        
        Args:
            result: RAG query result
            include_header: Whether to include section header
            
        Returns:
            Formatted context string
        """
        if not result.context:
            return ""
        
        if include_header:
            header = "## Relevant Underwriting Policies\n\n"
            if result.used_fallback:
                header += "(Full policy context - RAG unavailable)\n\n"
            return header + result.context
        
        return result.context
    
    def get_citations_for_response(
        self,
        result: RAGQueryResult,
    ) -> list[dict]:
        """
        Extract citations for inclusion in chat response metadata.
        
        Args:
            result: RAG query result
            
        Returns:
            List of citation dicts with policy_id, name, chunk_type
        """
        if not result.rag_context:
            return []
        
        return [
            {
                "policy_id": c.policy_id,
                "policy_name": c.policy_name,
                "chunk_type": c.chunk_type,
                "criteria_id": c.criteria_id,
            }
            for c in result.rag_context.citations
        ]


# Singleton instance for app-wide usage
_rag_service: RAGService | None = None


async def get_rag_service(settings: Settings | None = None) -> RAGService:
    """
    Get or create the RAG service singleton.
    
    Args:
        settings: Optional settings override
        
    Returns:
        Initialized RAGService instance
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService(settings=settings)
        await _rag_service.initialize()
    
    return _rag_service


async def close_rag_service() -> None:
    """Close the RAG service and release resources."""
    global _rag_service
    
    if _rag_service is not None:
        # Pool is managed separately
        _rag_service = None
