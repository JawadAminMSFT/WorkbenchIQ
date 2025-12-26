"""
RAG (Retrieval-Augmented Generation) package for policy search.

This package provides:
- PolicyChunker: Splits policies into searchable chunks
- EmbeddingService: Generates vector embeddings via Azure OpenAI
- PolicyChunkRepository: CRUD operations for policy chunks in PostgreSQL
- PolicyIndexer: Orchestrates the indexing pipeline
- PolicySearchService: Semantic search over policy chunks
- CategoryInference: Infers categories from natural language queries
- RAGContextBuilder: Assembles search results into LLM context
- RAGService: Unified service for RAG-enhanced chat
"""

from app.rag.chunker import PolicyChunker, PolicyChunk
from app.rag.embeddings import EmbeddingService
from app.rag.repository import PolicyChunkRepository
from app.rag.indexer import PolicyIndexer
from app.rag.search import PolicySearchService, SearchResult
from app.rag.inference import CategoryInference, InferredContext
from app.rag.context import RAGContextBuilder, RAGContext, PolicyCitation
from app.rag.service import RAGService, RAGQueryResult, get_rag_service, close_rag_service

__all__ = [
    "PolicyChunker",
    "PolicyChunk",
    "EmbeddingService",
    "PolicyChunkRepository",
    "PolicyIndexer",
    "PolicySearchService",
    "SearchResult",
    "CategoryInference",
    "InferredContext",
    "RAGContextBuilder",
    "RAGContext",
    "PolicyCitation",
    "RAGService",
    "RAGQueryResult",
    "get_rag_service",
    "close_rag_service",
]
