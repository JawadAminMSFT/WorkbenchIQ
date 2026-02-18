"""
Claims Policy Chunker - Splits automotive claims policies into searchable chunks.

Each claims policy is split into multiple chunks:
- policy_header: Overview with name, description, category
- criteria: One chunk per evaluation criterion
- modifying_factor: Risk modifiers (combined into one chunk)
- reference: External references (combined into one chunk)

This mirrors the approach in app/rag/chunker.py but for automotive claims policies.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.claims.policies import ClaimsPolicy, PolicyCriterion, ModifyingFactor


@dataclass
class ClaimsPolicyChunk:
    """Represents a single chunk of claims policy content."""

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
    severity: str | None = None  # For damage policies
    risk_level: str | None = None  # For fraud policies
    liability_determination: str | None = None  # For liability policies
    action_recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Set after embedding
    embedding: list[float] | None = None


class ClaimsPolicyChunker:
    """
    Chunks automotive claims policies into searchable segments.

    Chunking strategy:
    1. policy_header: Policy overview (name, description, category context)
    2. criteria: One chunk per evaluation criterion with full context
    3. modifying_factor: Combined modifying factors
    4. reference: Combined references (if present)
    """

    def __init__(self, policy_version: str = "1.0"):
        self.policy_version = policy_version

    def chunk_policy(self, policy: ClaimsPolicy) -> list[ClaimsPolicyChunk]:
        """
        Chunk a single claims policy into multiple searchable segments.

        Args:
            policy: ClaimsPolicy object from the policy loader

        Returns:
            List of ClaimsPolicyChunk objects
        """
        chunks: list[ClaimsPolicyChunk] = []
        sequence = 0

        # 1. Policy header chunk
        header_chunk = self._chunk_policy_header(policy, sequence)
        chunks.append(header_chunk)
        sequence += 1

        # 2. Criteria chunks (one per criterion)
        for criterion in policy.criteria:
            criteria_chunk = self._chunk_criteria(policy, criterion, sequence)
            chunks.append(criteria_chunk)
            sequence += 1

        # 3. Modifying factors chunk
        if policy.modifying_factors:
            factors_chunk = self._chunk_modifying_factors(policy, sequence)
            chunks.append(factors_chunk)
            sequence += 1

        # 4. References chunk (if present)
        if policy.references:
            ref_chunk = self._chunk_references(policy, sequence)
            chunks.append(ref_chunk)
            sequence += 1

        return chunks

    def chunk_policies(self, policies: list[ClaimsPolicy]) -> list[ClaimsPolicyChunk]:
        """
        Chunk multiple claims policies.

        Args:
            policies: List of ClaimsPolicy objects

        Returns:
            List of all ClaimsPolicyChunk objects
        """
        all_chunks: list[ClaimsPolicyChunk] = []
        for policy in policies:
            chunks = self.chunk_policy(policy)
            all_chunks.extend(chunks)
        return all_chunks

    def _chunk_policy_header(
        self, policy: ClaimsPolicy, sequence: int
    ) -> ClaimsPolicyChunk:
        """Create a header chunk with policy overview."""
        # Build rich header content for semantic search
        content_parts = [
            f"Policy: {policy.name}",
            f"Category: {policy.category}",
        ]

        if policy.subcategory:
            content_parts.append(f"Subcategory: {policy.subcategory}")

        content_parts.append(f"Description: {policy.description}")

        # Add summary of what this policy covers
        if policy.category == "damage_assessment":
            content_parts.append(
                "This policy provides guidelines for assessing vehicle damage "
                "severity and determining repair requirements."
            )
        elif policy.category == "liability":
            content_parts.append(
                "This policy provides guidelines for determining fault and "
                "liability percentage in automotive accidents."
            )
        elif policy.category == "fraud_detection":
            content_parts.append(
                "This policy provides guidelines for identifying potential "
                "fraudulent claims and red flag indicators."
            )
        elif policy.category == "payout_calculation":
            content_parts.append(
                "This policy provides guidelines for validating repair estimates "
                "and calculating appropriate claim payouts."
            )

        content = "\n".join(content_parts)

        return ClaimsPolicyChunk(
            policy_id=policy.id,
            policy_version=self.policy_version,
            policy_name=policy.name,
            chunk_type="policy_header",
            chunk_sequence=sequence,
            category=policy.category,
            subcategory=policy.subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "criteria_count": len(policy.criteria),
                "modifying_factors_count": len(policy.modifying_factors),
            },
        )

    def _chunk_criteria(
        self, policy: ClaimsPolicy, criterion: PolicyCriterion, sequence: int
    ) -> ClaimsPolicyChunk:
        """Create a chunk for a single criterion."""
        # Build rich content with context
        content_parts = [
            f"Policy: {policy.name}",
            f"Criterion ID: {criterion.id}",
            f"Condition: {criterion.condition}",
            f"Action: {criterion.action}",
            f"Rationale: {criterion.rationale}",
        ]

        # Add type-specific fields
        if criterion.severity:
            content_parts.insert(3, f"Severity: {criterion.severity}")
        if criterion.risk_level:
            content_parts.insert(3, f"Risk Level: {criterion.risk_level}")
        if criterion.liability_determination:
            content_parts.insert(3, f"Liability: {criterion.liability_determination}")

        content = "\n".join(content_parts)

        return ClaimsPolicyChunk(
            policy_id=policy.id,
            policy_version=self.policy_version,
            policy_name=policy.name,
            chunk_type="criteria",
            chunk_sequence=sequence,
            category=policy.category,
            subcategory=policy.subcategory,
            criteria_id=criterion.id,
            severity=criterion.severity,
            risk_level=criterion.risk_level,
            liability_determination=criterion.liability_determination,
            action_recommendation=criterion.action,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "condition": criterion.condition,
                "action": criterion.action,
            },
        )

    def _chunk_modifying_factors(
        self, policy: ClaimsPolicy, sequence: int
    ) -> ClaimsPolicyChunk:
        """Create a chunk combining all modifying factors."""
        content_parts = [
            f"Policy: {policy.name}",
            "Modifying Factors:",
        ]

        for factor in policy.modifying_factors:
            content_parts.append(f"- {factor.factor}: {factor.impact}")

        content = "\n".join(content_parts)

        return ClaimsPolicyChunk(
            policy_id=policy.id,
            policy_version=self.policy_version,
            policy_name=policy.name,
            chunk_type="modifying_factor",
            chunk_sequence=sequence,
            category=policy.category,
            subcategory=policy.subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "factor_count": len(policy.modifying_factors),
                "factors": [f.factor for f in policy.modifying_factors],
            },
        )

    def _chunk_references(
        self, policy: ClaimsPolicy, sequence: int
    ) -> ClaimsPolicyChunk:
        """Create a chunk combining all references."""
        content_parts = [
            f"Policy: {policy.name}",
            "References:",
        ]

        for ref in policy.references:
            content_parts.append(f"- {ref}")

        content = "\n".join(content_parts)

        return ClaimsPolicyChunk(
            policy_id=policy.id,
            policy_version=self.policy_version,
            policy_name=policy.name,
            chunk_type="reference",
            chunk_sequence=sequence,
            category=policy.category,
            subcategory=policy.subcategory,
            content=content,
            content_hash=self._hash_content(content),
            token_count=self._estimate_tokens(content),
            metadata={
                "reference_count": len(policy.references),
            },
        )

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content for change detection."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _estimate_tokens(self, content: str) -> int:
        """
        Estimate token count using simple heuristic.
        
        Rough estimate: 1 token ≈ 4 characters for English text.
        """
        return len(content) // 4
