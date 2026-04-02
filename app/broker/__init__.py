"""
Commercial Brokerage Module

This module provides data models and storage for the commercial insurance
brokerage persona, covering clients, submissions, carrier quotes,
placement scoring, and carrier profiles.
"""

from app.broker.constants import (
    CoverageAdequacy,
    DocumentType,
    LineOfBusiness,
    PremiumBenchmark,
    QuoteStatus,
    SubmissionStatus,
)
from app.broker.models import (
    BrokerDocument,
    CarrierProfile,
    Client,
    DashboardMetrics,
    LossHistoryEntry,
    Placement,
    PlacementScoring,
    PropertyLocation,
    Quote,
    QuoteFields,
    Submission,
)
from app.broker.storage import BrokerStorage
from app.broker.quote_extractor import QuoteExtractor
from app.broker.placement_engine import PlacementEngine
from app.broker.research_engine import ClientResearchEngine
from app.broker.submission_generator import SubmissionGenerator

__all__ = [
    # Constants / enums
    "SubmissionStatus",
    "QuoteStatus",
    "LineOfBusiness",
    "DocumentType",
    "CoverageAdequacy",
    "PremiumBenchmark",
    # Models
    "PropertyLocation",
    "LossHistoryEntry",
    "Client",
    "BrokerDocument",
    "QuoteFields",
    "PlacementScoring",
    "Quote",
    "Submission",
    "Placement",
    "CarrierProfile",
    "DashboardMetrics",
    # Storage
    "BrokerStorage",
    # Processing engines
    "QuoteExtractor",
    "PlacementEngine",
    "ClientResearchEngine",
    "SubmissionGenerator",
]
