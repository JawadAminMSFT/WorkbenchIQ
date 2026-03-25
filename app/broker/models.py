"""
Data models for the Commercial Brokerage persona.

Defines dataclasses for clients, submissions, quotes, placements,
carrier profiles, and dashboard metrics.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.broker.constants import (
    CoverageAdequacy,
    DocumentType,
    LineOfBusiness,
    PremiumBenchmark,
    QuoteStatus,
    SubmissionStatus,
)


@dataclass
class PropertyLocation:
    address: str = ""
    occupancy: str = ""
    construction: str = ""
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    building_value: str = ""
    contents_value: str = ""
    bi_value: str = ""
    protection_class: str = ""


@dataclass
class LossHistoryEntry:
    date: Optional[str] = None
    cause_of_loss: str = ""
    amount_paid: str = ""
    description: str = ""


@dataclass
class Client:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    industry_code: str = ""
    business_type: str = ""
    years_in_business: Optional[int] = None
    annual_revenue: str = ""
    employee_count: Optional[int] = None
    headquarters_address: str = ""
    property_locations: List[PropertyLocation] = field(default_factory=list)
    renewal_date: Optional[str] = None
    broker_notes: str = ""
    research_brief: Optional[Dict[str, Any]] = None
    contacts: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class BrokerDocument:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    submission_id: str = ""
    document_type: str = DocumentType.OTHER.value
    file_name: str = ""
    blob_url: str = ""
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class QuoteFields:
    """Canonical quote fields extracted from carrier documents."""

    annual_premium: str = ""
    total_insured_value: str = ""
    building_limit: str = ""
    contents_limit: str = ""
    business_interruption_limit: str = ""
    deductible: str = ""
    flood_sublimit: str = ""
    earthquake_sublimit: str = ""
    named_perils_exclusions: List[str] = field(default_factory=list)
    special_conditions: List[str] = field(default_factory=list)
    policy_period: str = ""
    carrier_am_best_rating: str = ""
    quote_reference_number: str = ""
    expiry_date: Optional[str] = None
    underwriter: str = ""


@dataclass
class PlacementScoring:
    """AI-computed placement fields."""

    placement_score: float = 0.0
    placement_rank: int = 0
    recommendation_rationale: str = ""
    coverage_adequacy: str = CoverageAdequacy.ADEQUATE.value
    coverage_gaps: List[str] = field(default_factory=list)
    premium_percentile: str = PremiumBenchmark.MARKET.value


@dataclass
class Quote:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    submission_id: str = ""
    carrier_name: str = ""
    source_format: str = ""  # pdf, xlsx, email, portal
    source_file_name: str = ""
    received_date: Optional[str] = None
    status: str = QuoteStatus.RAW.value
    fields: QuoteFields = field(default_factory=QuoteFields)
    scoring: PlacementScoring = field(default_factory=PlacementScoring)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Submission:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = ""
    line_of_business: str = LineOfBusiness.PROPERTY.value
    acord_form_types: List[str] = field(default_factory=lambda: ["125", "140"])
    status: str = SubmissionStatus.DRAFT.value
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    total_insured_value: str = ""
    coverage_requested: Dict[str, Any] = field(default_factory=dict)
    submitted_carriers: List[str] = field(default_factory=list)
    documents: List[BrokerDocument] = field(default_factory=list)
    quotes: List[Quote] = field(default_factory=list)
    submission_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    # Extracted ACORD fields
    acord_125_fields: Dict[str, Any] = field(default_factory=dict)
    acord_140_fields: Dict[str, Any] = field(default_factory=dict)
    acord_field_confidence: Dict[str, float] = field(default_factory=dict)


@dataclass
class Placement:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = ""
    submission_id: str = ""
    selected_quote_ids: List[str] = field(default_factory=list)
    total_annual_premium: str = ""
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    placement_rationale: str = ""
    bound_date: Optional[str] = None
    broker_notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CarrierProfile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    carrier_name: str = ""
    amb_number: str = ""
    naic_code: str = ""
    financial_strength_rating: str = ""
    issuer_credit_rating: str = ""
    rating_outlook: str = ""
    balance_sheet_strength: str = ""
    operating_performance: str = ""
    business_profile: str = ""
    erm_assessment: str = ""
    net_premiums_written: str = ""
    policyholders_surplus: str = ""
    combined_ratio: str = ""
    five_year_avg_combined_ratio: str = ""
    report_date: Optional[str] = None
    # MD&A fields (16 additional fields per spec)
    direct_written_premium: str = ""
    dwp_growth_rate: str = ""
    net_premiums_earned: str = ""
    total_admitted_assets: str = ""
    total_invested_assets: str = ""
    loss_and_lae_reserves: str = ""
    unearned_premiums: str = ""
    rbc_total_adjusted_capital: str = ""
    rbc_control_level: str = ""
    nwp_to_surplus_ratio: str = ""
    reinsurance_per_risk_retention: str = ""
    cat_retention: str = ""
    reinsurance_cession_rate: str = ""
    lines_of_business_written: List[Dict[str, str]] = field(default_factory=list)
    geographic_concentration: List[Dict[str, str]] = field(default_factory=list)
    mda_year: str = ""
    net_income: str = ""
    underwriting_gain_loss: str = ""
    net_investment_income: str = ""


@dataclass
class DashboardMetrics:
    total_accounts: int = 0
    total_bound_premium: str = "$0"
    open_submissions: int = 0
    renewals_due_90_days: int = 0
    stale_submissions: int = 0  # No activity >7 days
