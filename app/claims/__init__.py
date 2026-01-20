"""
Claims Policy Engine Package for Automotive Claims

This package implements the policy-based claims rating and payout calculation
for automotive insurance claims.

Modules:
- policies: Loads and manages claims policies from JSON
- engine: Evaluates claims against policy rules
- chunker: Chunks policies for RAG indexing
- indexer: Indexes policy chunks with embeddings
- search: Semantic search over claims policies
"""

# Severity rating constants
SEVERITY_MINIMAL = "Minimal"
SEVERITY_MINOR = "Minor"
SEVERITY_MODERATE = "Moderate"
SEVERITY_HEAVY = "Heavy"
SEVERITY_TOTAL_LOSS = "Total Loss"

# Liability determination constants
LIABILITY_CLEAR = "Clear Liability"
LIABILITY_SHARED = "Shared"
LIABILITY_DISPUTED = "Disputed"

# Fraud risk levels
FRAUD_RISK_LOW = "Low"
FRAUD_RISK_MODERATE = "Moderate"
FRAUD_RISK_HIGH = "High"

# Import policy loader and engine classes
from app.claims.policies import (
    ClaimsPolicy,
    ClaimsPolicyDocument,
    ClaimsPolicyLoader,
    ModifyingFactor,
    PolicyCriterion,
)
from app.claims.engine import (
    ClaimAssessment,
    ClaimsPolicyEngine,
    DamageAssessment,
    FraudAssessment,
    LiabilityAssessment,
    PayoutAssessment,
    PolicyCitation,
)
from app.claims.chunker import (
    ClaimsPolicyChunk,
    ClaimsPolicyChunker,
)
from app.claims.indexer import (
    ClaimsPolicyChunkRepository,
    ClaimsPolicyIndexer,
)
from app.claims.search import (
    ClaimsPolicySearchService,
    ClaimsSearchResult,
    get_claims_policy_context,
)

# API router is imported lazily to avoid circular imports
# Use: from app.claims.api import router as claims_api_router
def get_claims_api_router():
    """Get claims API router (lazy import to avoid circular imports)."""
    from app.claims.api import router
    return router

# Public exports
__all__ = [
    # Severity constants
    "SEVERITY_MINIMAL",
    "SEVERITY_MINOR",
    "SEVERITY_MODERATE",
    "SEVERITY_HEAVY",
    "SEVERITY_TOTAL_LOSS",
    # Liability constants
    "LIABILITY_CLEAR",
    "LIABILITY_SHARED",
    "LIABILITY_DISPUTED",
    # Fraud risk constants
    "FRAUD_RISK_LOW",
    "FRAUD_RISK_MODERATE",
    "FRAUD_RISK_HIGH",
    # Policy loader classes
    "ClaimsPolicyLoader",
    "ClaimsPolicyDocument",
    "ClaimsPolicy",
    "PolicyCriterion",
    "ModifyingFactor",
    # Policy engine classes
    "ClaimsPolicyEngine",
    "ClaimAssessment",
    "DamageAssessment",
    "LiabilityAssessment",
    "FraudAssessment",
    "PayoutAssessment",
    "PolicyCitation",
    # RAG classes
    "ClaimsPolicyChunk",
    "ClaimsPolicyChunker",
    "ClaimsPolicyChunkRepository",
    "ClaimsPolicyIndexer",
    "ClaimsPolicySearchService",
    "ClaimsSearchResult",
    "get_claims_policy_context",
    # API Router (lazy loading)
    "get_claims_api_router",
]
