"""
RAG Context Builder - Assembles search results into LLM-ready context.

Formats policy chunks for inclusion in LLM prompts with token budget management.
"""

from __future__ import annotations

import tiktoken
from dataclasses import dataclass, field
from typing import Any

from app.rag.search import SearchResult
from app.utils import setup_logging

logger = setup_logging()

# Default token budgets
DEFAULT_MAX_TOKENS = 4000
DEFAULT_CHUNK_OVERHEAD = 50  # tokens for formatting per chunk


@dataclass
class PolicyCitation:
    """Citation reference for a policy chunk used in context."""
    
    policy_id: str
    policy_name: str
    chunk_type: str
    criteria_id: str | None
    category: str
    risk_level: str | None
    similarity: float
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "chunk_type": self.chunk_type,
            "criteria_id": self.criteria_id,
            "category": self.category,
            "risk_level": self.risk_level,
            "similarity": round(self.similarity, 3),
        }
    
    def __str__(self) -> str:
        """Human-readable citation string."""
        parts = [f"[{self.policy_id}]"]
        if self.criteria_id:
            parts.append(f"Criteria {self.criteria_id}")
        parts.append(f"({self.chunk_type})")
        return " ".join(parts)


@dataclass
class RAGContext:
    """Assembled RAG context ready for LLM prompt injection."""
    
    context_text: str
    citations: list[PolicyCitation]
    total_tokens: int
    chunks_included: int
    chunks_truncated: int
    categories_covered: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "context_text": self.context_text,
            "citations": [c.to_dict() for c in self.citations],
            "total_tokens": self.total_tokens,
            "chunks_included": self.chunks_included,
            "chunks_truncated": self.chunks_truncated,
            "categories_covered": self.categories_covered,
        }


class RAGContextBuilder:
    """
    Builds LLM-ready context from search results.
    
    Features:
    - Token budget management
    - Policy deduplication
    - Citation tracking
    - Structured formatting
    - Persona-aware headers
    """
    
    # Persona-specific policy type labels
    PERSONA_POLICY_LABELS = {
        "underwriting": "UNDERWRITING POLICIES",
        "life_health_claims": "CLAIMS PROCESSING POLICIES",
        "automotive_claims": "AUTO CLAIMS POLICIES",
        "property_casualty_claims": "PROPERTY & CASUALTY POLICIES",
    }
    
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model: str = "gpt-4",
        persona: str = "underwriting",
    ):
        """
        Initialize context builder.
        
        Args:
            max_tokens: Maximum tokens for assembled context
            model: Model name for tokenization (affects token counting)
            persona: Persona type for context header customization
        """
        self.max_tokens = max_tokens
        self.persona = persona
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base (GPT-4 family)
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def assemble_context(
        self,
        results: list[SearchResult],
        query: str | None = None,
        include_metadata: bool = True,
        format_style: str = "structured",
    ) -> RAGContext:
        """
        Assemble search results into LLM context.
        
        Args:
            results: List of SearchResult from search
            query: Original query (for context header)
            include_metadata: Whether to include chunk metadata
            format_style: 'structured', 'compact', or 'prose'
            
        Returns:
            RAGContext with assembled text and citations
        """
        if not results:
            return RAGContext(
                context_text="No relevant policy information found.",
                citations=[],
                total_tokens=0,
                chunks_included=0,
                chunks_truncated=0,
                categories_covered=[],
            )
        
        # Track what we include
        citations: list[PolicyCitation] = []
        chunks_included = 0
        chunks_truncated = 0
        categories_seen: set[str] = set()
        
        # Build context with token budget
        context_parts: list[str] = []
        tokens_used = 0
        
        # Header
        header = self._format_header(query, format_style)
        header_tokens = self.count_tokens(header)
        tokens_used += header_tokens
        context_parts.append(header)
        
        # Process each result within token budget
        for result in results:
            # Format this chunk
            chunk_text = self._format_chunk(result, include_metadata, format_style)
            chunk_tokens = self.count_tokens(chunk_text) + DEFAULT_CHUNK_OVERHEAD
            
            # Check if we have room
            if tokens_used + chunk_tokens > self.max_tokens:
                # Try to truncate the chunk
                remaining_tokens = self.max_tokens - tokens_used - DEFAULT_CHUNK_OVERHEAD
                if remaining_tokens > 100:  # Worth including partial
                    truncated_text = self._truncate_to_tokens(chunk_text, remaining_tokens)
                    context_parts.append(truncated_text)
                    tokens_used += self.count_tokens(truncated_text) + DEFAULT_CHUNK_OVERHEAD
                    chunks_included += 1
                    chunks_truncated += 1
                    
                    # Still add citation for partial content
                    citations.append(self._create_citation(result))
                    categories_seen.add(result.category)
                
                # Stop adding more chunks
                break
            
            # Add full chunk
            context_parts.append(chunk_text)
            tokens_used += chunk_tokens
            chunks_included += 1
            
            citations.append(self._create_citation(result))
            categories_seen.add(result.category)
        
        # Footer
        footer = self._format_footer(citations, format_style)
        context_parts.append(footer)
        tokens_used += self.count_tokens(footer)
        
        context_text = "\n\n".join(context_parts)
        
        logger.info(
            f"Assembled context: {chunks_included} chunks, "
            f"{tokens_used} tokens, {len(categories_seen)} categories"
        )
        
        return RAGContext(
            context_text=context_text,
            citations=citations,
            total_tokens=tokens_used,
            chunks_included=chunks_included,
            chunks_truncated=chunks_truncated,
            categories_covered=sorted(categories_seen),
        )
    
    def _format_header(self, query: str | None, style: str) -> str:
        """Format context header with persona-aware labels."""
        policy_label = self.PERSONA_POLICY_LABELS.get(
            self.persona, 
            "RELEVANT POLICIES"
        )
        
        if style == "compact":
            return f"=== RELEVANT {policy_label} ==="
        elif style == "prose":
            return f"The following {policy_label.lower()} are relevant to this assessment:"
        else:  # structured
            header = f"### Relevant {policy_label.title()} Context\n"
            if query:
                header += f"Query: {query}\n"
            return header
    
    def _format_chunk(
        self,
        result: SearchResult,
        include_metadata: bool,
        style: str,
    ) -> str:
        """Format a single chunk for context."""
        if style == "compact":
            # Minimal formatting
            lines = [f"[{result.policy_id}]"]
            if result.criteria_id:
                lines[0] += f" - Criteria {result.criteria_id}"
            lines.append(result.content)
            if result.action_recommendation:
                lines.append(f"Action: {result.action_recommendation}")
            return "\n".join(lines)
        
        elif style == "prose":
            # Narrative style
            text = f"According to policy {result.policy_name} ({result.policy_id})"
            if result.criteria_id:
                text += f", criteria {result.criteria_id}"
            text += f": {result.content}"
            if result.action_recommendation:
                text += f" Recommended action: {result.action_recommendation}"
            return text
        
        else:  # structured
            lines = [f"**Policy: {result.policy_name}** [{result.policy_id}]"]
            
            if include_metadata:
                meta_parts = [f"Category: {result.category}"]
                if result.subcategory:
                    meta_parts.append(f"Subcategory: {result.subcategory}")
                if result.risk_level:
                    meta_parts.append(f"Risk Level: {result.risk_level}")
                if result.chunk_type != "policy_header":
                    meta_parts.append(f"Type: {result.chunk_type}")
                lines.append(" | ".join(meta_parts))
            
            if result.criteria_id:
                lines.append(f"Criteria ID: {result.criteria_id}")
            
            lines.append(f"\n{result.content}")
            
            if result.action_recommendation:
                lines.append(f"\n**Recommendation:** {result.action_recommendation}")
            
            return "\n".join(lines)
    
    def _format_footer(
        self,
        citations: list[PolicyCitation],
        style: str,
    ) -> str:
        """Format context footer with citations."""
        if not citations:
            return ""
        
        if style == "compact":
            policy_ids = sorted(set(c.policy_id for c in citations))
            return f"Sources: {', '.join(policy_ids)}"
        
        elif style == "prose":
            policy_ids = sorted(set(c.policy_id for c in citations))
            return f"This information is based on policies: {', '.join(policy_ids)}."
        
        else:  # structured
            lines = ["---", "**Sources:**"]
            seen_policies: set[str] = set()
            for citation in citations:
                if citation.policy_id not in seen_policies:
                    seen_policies.add(citation.policy_id)
                    lines.append(f"- {citation.policy_id}: {citation.policy_name}")
            return "\n".join(lines)
    
    def _create_citation(self, result: SearchResult) -> PolicyCitation:
        """Create citation from search result."""
        return PolicyCitation(
            policy_id=result.policy_id,
            policy_name=result.policy_name,
            chunk_type=result.chunk_type,
            criteria_id=result.criteria_id,
            category=result.category,
            risk_level=result.risk_level,
            similarity=result.similarity,
        )
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token budget."""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        truncated_text = self.encoding.decode(truncated_tokens)
        
        # Add ellipsis to indicate truncation
        return truncated_text.rstrip() + "..."
    
    def estimate_tokens_needed(self, results: list[SearchResult]) -> int:
        """
        Estimate tokens needed for given results.
        
        Useful for planning token budgets before assembly.
        
        Args:
            results: Search results to estimate
            
        Returns:
            Estimated token count
        """
        total = 0
        for result in results:
            # Rough estimate based on content length
            total += self.count_tokens(result.content)
            total += DEFAULT_CHUNK_OVERHEAD
        
        # Add header/footer overhead
        total += 100
        
        return total
