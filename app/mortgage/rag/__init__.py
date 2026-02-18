"""
Mortgage RAG Integration Module.

Provides:
- MortgagePolicyChunker: Chunks OSFI B-20 and mortgage policies for indexing
- MortgagePolicyChunkStorage: PostgreSQL storage for policy chunks
"""

from app.mortgage.rag.chunker import MortgagePolicyChunker, MortgagePolicyChunk
from app.mortgage.rag.storage import MortgagePolicyChunkStorage

__all__ = [
    "MortgagePolicyChunker",
    "MortgagePolicyChunk",
    "MortgagePolicyChunkStorage",
]
