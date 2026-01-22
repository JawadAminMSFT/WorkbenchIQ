"""
Claims Policy Loader

This module provides functionality to load and query automotive claims policies
from JSON files. The policies define rules for damage assessment, liability
determination, fraud detection, and payout calculation.

Usage:
    loader = ClaimsPolicyLoader()
    policies = loader.load_policies("prompts/automotive-claims-policies.json")
    damage_policies = loader.get_policies_by_category("damage_assessment")
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ModifyingFactor:
    """A factor that can modify how a policy criterion is applied."""

    factor: str
    impact: str


@dataclass
class PolicyCriterion:
    """A single criterion within a claims policy."""

    id: str
    condition: str
    action: str
    rationale: str
    # Optional fields that vary by policy type
    severity: Optional[str] = None  # For damage assessment
    risk_level: Optional[str] = None  # For fraud detection
    liability_determination: Optional[str] = None  # For liability policies


@dataclass
class ClaimsPolicy:
    """
    Represents a single claims policy with its criteria and modifying factors.

    Policies cover categories like:
    - damage_assessment: Rating vehicle damage severity
    - liability: Determining fault and liability percentage
    - fraud_detection: Identifying potential fraud indicators
    - payout_calculation: Validating estimates and calculating payouts
    """

    id: str
    category: str
    subcategory: str
    name: str
    description: str
    criteria: list[PolicyCriterion] = field(default_factory=list)
    modifying_factors: list[ModifyingFactor] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class ClaimsPolicyDocument:
    """The complete claims policy document with metadata."""

    version: str
    effective_date: str
    description: str
    last_updated: str
    policies: list[ClaimsPolicy] = field(default_factory=list)


class ClaimsPolicyLoader:
    """
    Loads and manages automotive claims policies from JSON files.

    This class provides functionality to:
    - Load policies from JSON files
    - Query policies by category, subcategory, or ID
    - Cache loaded policies for performance

    Example:
        loader = ClaimsPolicyLoader()
        loader.load_policies("prompts/automotive-claims-policies.json")

        # Get all damage assessment policies
        damage_policies = loader.get_policies_by_category("damage_assessment")

        # Get a specific policy by ID
        severity_policy = loader.get_policy_by_id("DMG-SEV-001")
    """

    def __init__(self) -> None:
        """Initialize the policy loader with an empty cache."""
        self._document: Optional[ClaimsPolicyDocument] = None
        self._policies_by_category: dict[str, list[ClaimsPolicy]] = {}
        self._policies_by_id: dict[str, ClaimsPolicy] = {}

    @property
    def is_loaded(self) -> bool:
        """Check if policies have been loaded."""
        return self._document is not None

    @property
    def document(self) -> Optional[ClaimsPolicyDocument]:
        """Get the loaded policy document."""
        return self._document

    def load_policies(self, path: str | Path) -> ClaimsPolicyDocument:
        """
        Load policies from a JSON file.

        Args:
            path: Path to the claims policies JSON file.

        Returns:
            The loaded ClaimsPolicyDocument with all policies.

        Raises:
            FileNotFoundError: If the policy file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            ValueError: If the file structure is invalid.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._document = self._parse_document(data)
        self._build_indexes()
        return self._document

    def _parse_document(self, data: dict[str, Any]) -> ClaimsPolicyDocument:
        """Parse the raw JSON data into a structured document."""
        policies = []
        for policy_data in data.get("policies", []):
            policy = self._parse_policy(policy_data)
            policies.append(policy)

        return ClaimsPolicyDocument(
            version=data.get("version", "1.0"),
            effective_date=data.get("effective_date", ""),
            description=data.get("description", ""),
            last_updated=data.get("last_updated", ""),
            policies=policies,
        )

    def _parse_policy(self, data: dict[str, Any]) -> ClaimsPolicy:
        """Parse a single policy from JSON data."""
        criteria = []
        for criterion_data in data.get("criteria", []):
            criterion = PolicyCriterion(
                id=criterion_data.get("id", ""),
                condition=criterion_data.get("condition", ""),
                action=criterion_data.get("action", ""),
                rationale=criterion_data.get("rationale", ""),
                severity=criterion_data.get("severity"),
                risk_level=criterion_data.get("risk_level"),
                liability_determination=criterion_data.get("liability_determination"),
            )
            criteria.append(criterion)

        modifying_factors = []
        for factor_data in data.get("modifying_factors", []):
            factor = ModifyingFactor(
                factor=factor_data.get("factor", ""),
                impact=factor_data.get("impact", ""),
            )
            modifying_factors.append(factor)

        return ClaimsPolicy(
            id=data.get("id", ""),
            category=data.get("category", ""),
            subcategory=data.get("subcategory", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            criteria=criteria,
            modifying_factors=modifying_factors,
            references=data.get("references", []),
        )

    def _build_indexes(self) -> None:
        """Build internal indexes for fast policy lookup."""
        self._policies_by_category.clear()
        self._policies_by_id.clear()

        if self._document is None:
            return

        for policy in self._document.policies:
            # Index by category
            if policy.category not in self._policies_by_category:
                self._policies_by_category[policy.category] = []
            self._policies_by_category[policy.category].append(policy)

            # Index by ID
            self._policies_by_id[policy.id] = policy

    def get_policies_by_category(self, category: str) -> list[ClaimsPolicy]:
        """
        Get all policies in a specific category.

        Args:
            category: The category to filter by (e.g., "damage_assessment",
                     "liability", "fraud_detection", "payout_calculation").

        Returns:
            List of policies in the specified category. Returns empty list
            if category not found or policies not loaded.
        """
        return self._policies_by_category.get(category, [])

    def get_policies_by_subcategory(
        self, category: str, subcategory: str
    ) -> list[ClaimsPolicy]:
        """
        Get policies matching a specific category and subcategory.

        Args:
            category: The category to filter by.
            subcategory: The subcategory to filter by.

        Returns:
            List of policies matching both category and subcategory.
        """
        policies = self._policies_by_category.get(category, [])
        return [p for p in policies if p.subcategory == subcategory]

    def get_policy_by_id(self, policy_id: str) -> Optional[ClaimsPolicy]:
        """
        Get a specific policy by its ID.

        Args:
            policy_id: The unique policy identifier (e.g., "DMG-SEV-001").

        Returns:
            The matching policy or None if not found.
        """
        return self._policies_by_id.get(policy_id)

    def get_all_policies(self) -> list[ClaimsPolicy]:
        """
        Get all loaded policies.

        Returns:
            List of all policies in the document.
        """
        if self._document is None:
            return []
        return self._document.policies

    def get_categories(self) -> list[str]:
        """
        Get all unique policy categories.

        Returns:
            List of category names.
        """
        return list(self._policies_by_category.keys())

    def get_criterion_by_id(
        self, criterion_id: str
    ) -> Optional[tuple[ClaimsPolicy, PolicyCriterion]]:
        """
        Get a specific criterion by its ID.

        Criterion IDs follow the pattern: POLICY-ID-LETTER (e.g., "DMG-SEV-001-A").

        Args:
            criterion_id: The unique criterion identifier.

        Returns:
            Tuple of (policy, criterion) if found, None otherwise.
        """
        # Extract policy ID from criterion ID (e.g., "DMG-SEV-001" from "DMG-SEV-001-A")
        parts = criterion_id.rsplit("-", 1)
        if len(parts) != 2:
            return None

        policy_id = parts[0]
        policy = self.get_policy_by_id(policy_id)
        if policy is None:
            return None

        for criterion in policy.criteria:
            if criterion.id == criterion_id:
                return (policy, criterion)

        return None
