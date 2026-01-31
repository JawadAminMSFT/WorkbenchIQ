"""
Canadian Mortgage Underwriting Module

This module provides mortgage underwriting functionality with OSFI B-20 compliance
for Canadian residential mortgages.
"""

from app.mortgage.constants import (
    MortgageCaseStatus,
    MortgageDocType,
    MortgageProductType,
    PropertyType,
    PropertyOccupancy,
    EmploymentType,
    IncomeType,
    RateType,
    UnderwritingDecision,
    FindingSeverity,
    RiskLevel,
)
from app.mortgage.doc_classifier import MortgageDocClassifier
from app.mortgage.router import MortgageDocRouter
from app.mortgage.processor import MortgageDocProcessor, extract_field_provenance

# Phase 4: Data aggregation, provenance, and storage
from app.mortgage.aggregator import MortgageCaseAggregator
from app.mortgage.provenance import ProvenanceTracker
from app.mortgage.storage import MortgageStorage

# Phase 4: Field extractors
from app.mortgage.extractors import (
    extract_borrower_fields,
    extract_income_fields,
    extract_property_fields,
    extract_loan_fields,
    extract_credit_fields,
)

# Phase 5: Calculator and stress test
from app.mortgage.calculator import MortgageCalculator, CalculationResult
from app.mortgage.stress_test import OSFIStressTest, StressTestResult

# Phase 6: Policy engine
from app.mortgage.policy_engine import (
    MortgagePolicyEvaluator,
    RecommendationEngine,
    Finding,
    Recommendation,
)

# Phase 7: Risk analysis
from app.mortgage.risk_analysis import (
    IncomeConsistencyEngine,
    FraudDetectionEngine,
    AMLTriageEngine,
    CreditRiskEngine,
    RiskSignalAggregator,
    RiskSignal,
    RiskReport,
)

# Alias for backwards compatibility
MortgagePolicyEngine = MortgagePolicyEvaluator

__version__ = "1.0.0"


# Stub class for later phases
class MortgagePolicyLoader:
    """Loads and parses mortgage underwriting policies from JSON."""
    pass


__all__ = [
    # Phase 2: Document classification and routing
    "MortgageDocClassifier",
    "MortgageDocRouter",
    "MortgageDocProcessor",
    "extract_field_provenance",
    # Phase 4: Aggregation, provenance, and storage
    "MortgageCaseAggregator",
    "ProvenanceTracker",
    "MortgageStorage",
    # Phase 4: Field extractors
    "extract_borrower_fields",
    "extract_income_fields",
    "extract_property_fields",
    "extract_loan_fields",
    "extract_credit_fields",
    # Phase 5: Calculator and stress test
    "MortgageCalculator",
    "CalculationResult",
    "OSFIStressTest",
    "StressTestResult",
    # Phase 6: Policy engine
    "MortgagePolicyEvaluator",
    "MortgagePolicyEngine",  # Alias for backwards compatibility
    "RecommendationEngine",
    "Finding",
    "Recommendation",
    # Phase 7: Risk analysis
    "IncomeConsistencyEngine",
    "FraudDetectionEngine",
    "AMLTriageEngine",
    "CreditRiskEngine",
    "RiskSignalAggregator",
    "RiskSignal",
    "RiskReport",
    # Stub classes (to be implemented)
    "MortgagePolicyLoader",
    # Constants
    "MortgageCaseStatus",
    "MortgageDocType",
    "MortgageProductType",
    "PropertyType",
    "PropertyOccupancy",
    "EmploymentType",
    "IncomeType",
    "RateType",
    "UnderwritingDecision",
    "FindingSeverity",
    "RiskLevel",
]

