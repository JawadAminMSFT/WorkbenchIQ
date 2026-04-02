"""
Constants and enums for the Commercial Brokerage persona.

Defines statuses, line-of-business codes, document types, and scoring
categories used across the broker workflow.
"""

from enum import Enum


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    QUOTED = "quoted"
    BOUND = "bound"
    DECLINED = "declined"
    LAPSED = "lapsed"


class QuoteStatus(str, Enum):
    RAW = "raw"
    EXTRACTED = "extracted"
    REVIEWED = "reviewed"
    SELECTED = "selected"
    DECLINED = "declined"


class LineOfBusiness(str, Enum):
    PROPERTY = "property"
    D_AND_O = "d_and_o"
    WORKERS_COMP = "workers_comp"
    GENERAL_LIABILITY = "general_liability"
    BENEFITS = "benefits"


class DocumentType(str, Enum):
    ACORD_125 = "acord_125"
    ACORD_140 = "acord_140"
    SOV = "sov"
    LOSS_RUNS = "loss_runs"
    PROPERTY_PHOTOS = "property_photos"
    PRIOR_DECLARATION = "prior_declaration"
    SUBMISSION_EMAIL = "submission_email"
    CARRIER_QUOTE = "carrier_quote"
    OTHER = "other"


class CoverageAdequacy(str, Enum):
    ADEQUATE = "adequate"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class PremiumBenchmark(str, Enum):
    BELOW_MARKET = "below_market"
    MARKET = "market"
    ABOVE_MARKET = "above_market"
