"""
Mortgage Policy Chunker - Splits OSFI B-20 and mortgage policies into searchable chunks.

Optimized for Canadian mortgage underwriting content including:
- OSFI Guideline B-20 sections
- GDS/TDS ratio requirements
- MQR (Mortgage Qualifying Rate) rules
- Down payment requirements
- LTV restrictions
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MortgagePolicyChunk:
    """
    Represents a single chunk of mortgage policy content.
    
    Attributes:
        id: Unique chunk identifier
        content: The text content of the chunk
        source: Policy source (e.g., "OSFI B-20")
        chunk_index: Index of this chunk within the source
        section: Section identifier if applicable
        metadata: Additional metadata about the chunk
        embedding: Vector embedding (set after embedding)
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    source: str = ""
    chunk_index: int = 0
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        """Initialize metadata with source if not present."""
        if "source" not in self.metadata:
            self.metadata["source"] = self.source


class MortgagePolicyChunker:
    """
    Chunks mortgage policies into searchable segments.
    
    Supports chunking of:
    - OSFI Guideline B-20 text documents
    - Structured JSON policy files
    - Free-form policy text
    
    Chunking strategies:
    - Section-based: Split on section headers (Section X.X)
    - Paragraph-based: Split on double newlines
    - Semantic: Keep related concepts together
    """
    
    # Pattern to detect section headers like "Section 4.1" or "Section 4.1 - Title"
    # Allows leading whitespace for indented text
    SECTION_PATTERN = re.compile(
        r'^\s*(Section\s+\d+(?:\.\d+)?(?:\s*[-–—]\s*[^\n]+)?)',
        re.MULTILINE | re.IGNORECASE
    )
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 10,  # Low default to handle small test cases
        overlap: int = 50,
    ):
        """
        Initialize the chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters to form a chunk
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
    
    def chunk(
        self,
        policy_text: str,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MortgagePolicyChunk]:
        """
        Chunk policy text into searchable segments.
        
        Args:
            policy_text: The policy text to chunk
            source: Policy source identifier
            metadata: Additional metadata to attach to chunks
            
        Returns:
            List of MortgagePolicyChunk objects
        """
        if not policy_text or not policy_text.strip():
            return []
        
        metadata = metadata or {}
        chunks: List[MortgagePolicyChunk] = []
        
        # Try section-based chunking first
        sections = self._split_by_sections(policy_text)
        
        if len(sections) > 1:
            # Multiple sections found - chunk each section
            chunks = self._chunk_sections(sections, source, metadata)
        else:
            # No clear sections - use paragraph-based chunking
            chunks = self._chunk_paragraphs(policy_text, source, metadata)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Split text by section headers.
        
        Args:
            text: Policy text to split
            
        Returns:
            List of dicts with 'header' and 'content' keys
        """
        sections = []
        matches = list(self.SECTION_PATTERN.finditer(text))
        
        if not matches:
            return [{"header": None, "content": text.strip()}]
        
        for i, match in enumerate(matches):
            header = match.group(1).strip()
            start = match.end()
            
            # End at next section or end of text
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)
            
            content = text[start:end].strip()
            
            if content:
                sections.append({
                    "header": header,
                    "content": content,
                })
        
        # Check for content before first section
        if matches and matches[0].start() > 0:
            preamble = text[:matches[0].start()].strip()
            if preamble and len(preamble) >= self.min_chunk_size:
                sections.insert(0, {
                    "header": None,
                    "content": preamble,
                })
        
        return sections
    
    def _chunk_sections(
        self,
        sections: List[Dict[str, str]],
        source: str,
        metadata: Dict[str, Any],
    ) -> List[MortgagePolicyChunk]:
        """
        Convert sections to chunks.
        
        Large sections may be split further.
        """
        chunks = []
        chunk_index = 0
        
        for section in sections:
            header = section["header"]
            content = section["content"]
            
            # Include header in content for searchability
            if header:
                full_content = f"{header}\n\n{content}"
            else:
                full_content = content
            
            # Check if section needs further splitting
            if len(full_content) <= self.max_chunk_size:
                # Single chunk for this section
                chunk_metadata = {**metadata}
                if header:
                    chunk_metadata["section"] = header
                
                chunks.append(MortgagePolicyChunk(
                    content=full_content,
                    source=source,
                    chunk_index=chunk_index,
                    section=header,
                    metadata=chunk_metadata,
                ))
                chunk_index += 1
            else:
                # Split large section by paragraphs
                sub_chunks = self._chunk_paragraphs(
                    full_content, source, metadata, header
                )
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    chunk_index += 1
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_paragraphs(
        self,
        text: str,
        source: str,
        metadata: Dict[str, Any],
        section: Optional[str] = None,
    ) -> List[MortgagePolicyChunk]:
        """
        Chunk text by paragraphs.
        
        Paragraphs are joined until max_chunk_size is reached.
        """
        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_content = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Would adding this paragraph exceed the max?
            test_content = f"{current_content}\n\n{para}" if current_content else para
            
            if len(test_content) > self.max_chunk_size and current_content:
                # Save current chunk and start new one
                chunk_metadata = {**metadata}
                if section:
                    chunk_metadata["section"] = section
                
                chunks.append(MortgagePolicyChunk(
                    content=current_content,
                    source=source,
                    chunk_index=chunk_index,
                    section=section,
                    metadata=chunk_metadata,
                ))
                chunk_index += 1
                
                # Start new chunk with overlap if possible
                if self.overlap > 0 and len(current_content) > self.overlap:
                    overlap_text = current_content[-self.overlap:]
                    current_content = f"{overlap_text}\n\n{para}"
                else:
                    current_content = para
            else:
                current_content = test_content
        
        # Don't forget the last chunk
        if current_content and len(current_content) >= self.min_chunk_size:
            chunk_metadata = {**metadata}
            if section:
                chunk_metadata["section"] = section
            
            chunks.append(MortgagePolicyChunk(
                content=current_content,
                source=source,
                chunk_index=chunk_index,
                section=section,
                metadata=chunk_metadata,
            ))
        
        return chunks
    
    def chunk_json_policy(
        self,
        policy: Dict[str, Any],
        source: str = "",
    ) -> List[MortgagePolicyChunk]:
        """
        Chunk a JSON-structured policy.
        
        Args:
            policy: Policy dict with 'id', 'name', 'category', etc.
            source: Optional source override
            
        Returns:
            List of chunks
        """
        chunks = []
        chunk_index = 0
        
        policy_id = policy.get("id", "unknown")
        policy_name = policy.get("name", "Unknown Policy")
        category = policy.get("category", "general")
        description = policy.get("description", "")
        
        source = source or f"policy:{policy_id}"
        
        base_metadata = {
            "source": source,
            "policy_id": policy_id,
            "policy_name": policy_name,
            "category": category,
        }
        
        # Create header chunk
        header_content = f"Policy: {policy_name}\n\nCategory: {category}"
        if description:
            header_content += f"\n\n{description}"
        
        chunks.append(MortgagePolicyChunk(
            content=header_content,
            source=source,
            chunk_index=chunk_index,
            metadata={**base_metadata, "chunk_type": "policy_header"},
        ))
        chunk_index += 1
        
        # Create criteria chunks
        criteria_list = policy.get("evaluation_criteria", [])
        for criterion in criteria_list:
            criteria_content = self._format_criterion(criterion)
            criteria_metadata = {
                **base_metadata,
                "chunk_type": "criteria",
                "criteria_id": criterion.get("id"),
                "risk_level": criterion.get("risk_level"),
            }
            
            chunks.append(MortgagePolicyChunk(
                content=criteria_content,
                source=source,
                chunk_index=chunk_index,
                metadata=criteria_metadata,
            ))
            chunk_index += 1
        
        return chunks
    
    def _format_criterion(self, criterion: Dict[str, Any]) -> str:
        """Format a criterion for chunk content."""
        parts = []
        
        name = criterion.get("name", "Criterion")
        parts.append(f"Criterion: {name}")
        
        description = criterion.get("description", "")
        if description:
            parts.append(f"\n{description}")
        
        condition = criterion.get("condition", "")
        if condition:
            parts.append(f"\nCondition: {condition}")
        
        threshold = criterion.get("threshold")
        if threshold is not None:
            parts.append(f"\nThreshold: {threshold}")
        
        risk_level = criterion.get("risk_level", "")
        if risk_level:
            parts.append(f"\nRisk Level: {risk_level}")
        
        action = criterion.get("action_recommendation", "")
        if action:
            parts.append(f"\nRecommendation: {action}")
        
        return "".join(parts)
    
    def compute_content_hash(self, content: str) -> str:
        """Compute a hash of the content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
