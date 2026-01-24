"""
Persona-aware Policy Indexer Factory.

Routes indexing operations to the unified indexer with persona-specific configuration.
This provides a unified interface for policy RAG indexing across all personas.

NOTE: This module re-exports from unified_indexer for backwards compatibility.
New code should import directly from app.rag.unified_indexer.
"""

from __future__ import annotations

# Re-export everything from unified_indexer for backwards compatibility
from app.rag.unified_indexer import (
    UnifiedPolicyIndexer,
    UnifiedPolicyChunkRepository,
    PERSONA_CONFIG,
    IndexingError,
    get_indexer_for_persona,
    get_index_stats_for_persona,
    get_supported_personas,
    persona_supports_rag,
)

# Legacy mappings for backwards compatibility
PERSONA_POLICY_FILES = {
    persona: config["policies_path"]
    for persona, config in PERSONA_CONFIG.items()
}

PERSONA_POLICY_TABLES = {
    persona: config["table_name"]
    for persona, config in PERSONA_CONFIG.items()
}

# Type alias for backwards compatibility
PolicyIndexerProtocol = UnifiedPolicyIndexer

__all__ = [
    # New unified exports
    "UnifiedPolicyIndexer",
    "UnifiedPolicyChunkRepository",
    "PERSONA_CONFIG",
    "IndexingError",
    "get_indexer_for_persona",
    "get_index_stats_for_persona",
    "get_supported_personas",
    "persona_supports_rag",
    # Legacy exports
    "PERSONA_POLICY_FILES",
    "PERSONA_POLICY_TABLES",
    "PolicyIndexerProtocol",
]
