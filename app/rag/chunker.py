"""
Policy Chunker - Splits underwriting policies into searchable chunks.

Each policy is split into multiple chunks:
- policy_header: Overview with name, description, category
- criteria: One chunk per evaluation criteria
- modifying_factor: Risk modifiers (combined into one chunk)
- reference: External references (combined into one chunk)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyChunk:
    """Represents a single chunk of policy content."""
    
    policy_id: str
    policy_version: str
    policy_name: str
    chunk_type: str  # policy_header, criteria, modifying_factor, reference
    chunk_sequence: int
    category: str
    content: str
    content_hash: str
    token_count: int
    
    # Optional fields
    subcategory: str | None = None
    criteria_id: str | None = None
    risk_level: str | None = None
    action_recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Set after embedding
    embedding: list[float] | None = None


class PolicyChunker:
    """
    Chunks underwriting policies into searchable segments.
    
    Chunking strategy per data-model.md:
    1. policy_header: Policy overview (name, description, category context)
    2. criteria: One chunk per evaluation criteria with full context
    3. modifying_factor: Combined modifying factors
    4. reference: Combined references
    """
    
    def __init__(self, policy_version: str = "1.0"):
        self.policy_version = policy_version
    
    def chunk_policy(self, policy: dict[str, Any]) -> list[PolicyChunk]:
        """
        Chunk a single policy into multiple searchable segments.
        
        Args:
            policy: Policy dict from life-health-underwriting-policies.json
            
        Returns:
            List of PolicyChunk objects
        """
        chunks: list[PolicyChunk] = []
        sequence = 0
        
        policy_id = policy["id"]
        policy_name = policy["name"]
        category = policy["category"]
        subcategory = policy.get("subcategory")
        
        # 1. Policy header chunk
        header_chunk = self._chunk_policy_header(
            policy, sequence
        )
        chunks.append(header_chunk)
        sequence += 1
        
        # 2. Criteria chunks (one per criteria)
        for criteria in policy.get("criteria", []):
            criteria_chunk = self._chunk_criteria(
                policy_id, policy_name, category, subcategory,
                criteria, sequence
            )
            chunks.append(criteria_chunk)
            sequence += 1
        
        # 3. Modifying factors chunk
        if policy.get("modifying_factors"):
            factors_chunk = self._chunk_modifying_factors(
                policy_id, policy_name, category, subcategory,
                policy["modifying_factors"], sequence
            )
            chunks.append(factors_chunk)
            sequence += 1
        
        # 4. References chunk
        if policy.get("references"):
            refs_chunk = self._chunk_references(
                policy_id, policy_name, category, subcategory,
                policy["references"], sequence
            )
            chunks.append(refs_chunk)
            sequence += 1
        
        return chunks
    
    def _chunk_policy_header(
        self, policy: dict[str, Any], sequence: int
    ) -> PolicyChunk:
        """Create the policy header chunk with overview information."""
        policy_id = policy["id"]
        policy_name = policy["name"]
        category = policy["category"]
        subcategory = policy.get("subcategory")
        description = policy.get("description", "")
        
        # Build rich content for embedding
        content_parts = [
            f"Policy: {policy_name}",
            f"Category: {category}",
        ]
        if subcategory:
            content_parts.append(f"Subcategory: {subcategory}")
        if description:
            content_parts.append(f"Description: {description}")
        
        # Add criteria summary
        criteria_count = len(policy.get("criteria", []))
        if criteria_count:
            risk_levels = [c.get("risk_level") for c in policy.get("criteria", [])]
            content_parts.append(
                f"Contains {criteria_count} evaluation criteria covering risk levels: "
                f"{', '.join(sorted(set(r for r in risk_levels if r)))}"
            )
        
        content = "\n".join(content_parts)
        
        return PolicyChunk(
            policy_id=policy_id,
            policy_version=self.policy_version,
            policy_name=policy_name,
            chunk_type="policy_header",
            chunk_sequence=sequence,
            category=category,
            subcategory=subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "criteria_count": criteria_count,
                "has_modifying_factors": bool(policy.get("modifying_factors")),
                "has_references": bool(policy.get("references")),
            }
        )
    
    def _chunk_criteria(
        self,
        policy_id: str,
        policy_name: str,
        category: str,
        subcategory: str | None,
        criteria: dict[str, Any],
        sequence: int,
    ) -> PolicyChunk:
        """Create a chunk for a single evaluation criteria."""
        criteria_id = criteria.get("id", f"{policy_id}-{sequence}")
        condition = criteria.get("condition", "")
        risk_level = criteria.get("risk_level", "")
        action = criteria.get("action", "")
        rationale = criteria.get("rationale", "")
        
        # Build rich content with policy context
        content_parts = [
            f"Policy: {policy_name}",
            f"Condition: {condition}",
            f"Risk Level: {risk_level}",
            f"Action: {action}",
        ]
        if rationale:
            content_parts.append(f"Rationale: {rationale}")
        
        content = "\n".join(content_parts)
        
        return PolicyChunk(
            policy_id=policy_id,
            policy_version=self.policy_version,
            policy_name=policy_name,
            chunk_type="criteria",
            chunk_sequence=sequence,
            category=category,
            subcategory=subcategory,
            criteria_id=criteria_id,
            risk_level=risk_level,
            action_recommendation=action,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "condition": condition,
                "rationale": rationale,
            }
        )
    
    def _chunk_modifying_factors(
        self,
        policy_id: str,
        policy_name: str,
        category: str,
        subcategory: str | None,
        factors: list[dict[str, Any]],
        sequence: int,
    ) -> PolicyChunk:
        """Create a chunk for modifying factors."""
        content_parts = [
            f"Policy: {policy_name}",
            "Modifying Factors:",
        ]
        
        for factor in factors:
            factor_name = factor.get("factor", "")
            impact = factor.get("impact", "")
            content_parts.append(f"- {factor_name}: {impact}")
        
        content = "\n".join(content_parts)
        
        return PolicyChunk(
            policy_id=policy_id,
            policy_version=self.policy_version,
            policy_name=policy_name,
            chunk_type="modifying_factor",
            chunk_sequence=sequence,
            category=category,
            subcategory=subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "factor_count": len(factors),
                "factors": [f.get("factor") for f in factors],
            }
        )
    
    def _chunk_references(
        self,
        policy_id: str,
        policy_name: str,
        category: str,
        subcategory: str | None,
        references: list[str],
        sequence: int,
    ) -> PolicyChunk:
        """Create a chunk for references."""
        content_parts = [
            f"Policy: {policy_name}",
            "References:",
        ]
        for ref in references:
            content_parts.append(f"- {ref}")
        
        content = "\n".join(content_parts)
        
        return PolicyChunk(
            policy_id=policy_id,
            policy_version=self.policy_version,
            policy_name=policy_name,
            chunk_type="reference",
            chunk_sequence=sequence,
            category=category,
            subcategory=subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "reference_count": len(references),
            }
        )
    
    def chunk_all_policies(
        self, policies: list[dict[str, Any]]
    ) -> list[PolicyChunk]:
        """
        Chunk all policies from the policies list.
        
        Args:
            policies: List of policy dicts
            
        Returns:
            Flat list of all PolicyChunk objects
        """
        all_chunks: list[PolicyChunk] = []
        for policy in policies:
            chunks = self.chunk_policy(policy)
            all_chunks.extend(chunks)
        return all_chunks
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate SHA-256 hash for content change detection."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.
        
        Uses simple heuristic: ~4 characters per token for English text.
        For production, consider using tiktoken for accurate counts.
        """
        return len(text) // 4
