"""
Constants and enums for Canadian Mortgage Underwriting.
"""

from enum import Enum


class MortgageCaseStatus(str, Enum):
    """Status values for mortgage applications."""
    INTAKE = "intake"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    PENDING_DOCUMENTS = "pending_documents"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    FUNDED = "funded"


class MortgageDocType(str, Enum):
    """Document types for mortgage applications."""
    # Application documents
    APPLICATION = "application"
    CREDIT_REPORT = "credit_report"
    APPRAISAL = "appraisal"
    
    # Income documents
    PAYSTUB = "paystub"
    T4 = "t4"
    NOA = "noa"  # Notice of Assessment
    EMPLOYMENT_LETTER = "employment_letter"
    T1_GENERAL = "t1_general"  # Self-employed
    FINANCIAL_STATEMENTS = "financial_statements"  # Self-employed
    
    # Property documents
    PURCHASE_AGREEMENT = "purchase_agreement"
    PROPERTY_TAX_BILL = "property_tax_bill"
    TITLE_SEARCH = "title_search"
    HOMEOWNERS_INSURANCE = "homeowners_insurance"
    CONDO_DOCUMENTS = "condo_documents"
    
    # Asset/liability documents
    BANK_STATEMENTS = "bank_statements"
    RRSP_STATEMENT = "rrsp_statement"
    GIFT_LETTER = "gift_letter"
    DOWN_PAYMENT_VERIFICATION = "down_payment_verification"
    
    # Other
    ID_VERIFICATION = "id_verification"
    VOID_CHEQUE = "void_cheque"
    OTHER = "other"


class MortgageProductType(str, Enum):
    """Mortgage product types."""
    CONVENTIONAL = "conventional"  # LTV <= 80%
    HIGH_RATIO = "high_ratio"  # LTV > 80%, requires insurance
    CMHC_INSURED = "cmhc_insured"  # CMHC insurance
    GENWORTH_INSURED = "genworth_insured"  # Genworth insurance
    CANADA_GUARANTY_INSURED = "canada_guaranty_insured"  # Canada Guaranty
    REFINANCE = "refinance"
    RENEWAL = "renewal"
    SWITCH = "switch"  # Transfer to another lender


class PropertyType(str, Enum):
    """Property types for Canadian real estate."""
    SINGLE_FAMILY_DETACHED = "single_family_detached"
    SEMI_DETACHED = "semi_detached"
    TOWNHOUSE = "townhouse"
    CONDOMINIUM = "condominium"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    FOURPLEX = "fourplex"
    MOBILE_HOME = "mobile_home"
    MODULAR_HOME = "modular_home"
    MIXED_USE = "mixed_use"


class PropertyOccupancy(str, Enum):
    """Property occupancy types."""
    OWNER_OCCUPIED = "owner_occupied"  # Primary residence
    SECOND_HOME = "second_home"  # Vacation property
    INVESTMENT_RENTAL = "investment_rental"  # Rental property


class EmploymentType(str, Enum):
    """Employment types for income qualification."""
    PERMANENT_FULL_TIME = "permanent_full_time"
    PERMANENT_PART_TIME = "permanent_part_time"
    CONTRACT = "contract"
    SELF_EMPLOYED = "self_employed"
    COMMISSION = "commission"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"
    OTHER = "other"


class IncomeType(str, Enum):
    """Income source types."""
    SALARY = "salary"
    HOURLY = "hourly"
    BONUS = "bonus"
    COMMISSION = "commission"
    OVERTIME = "overtime"
    SELF_EMPLOYED = "self_employed"
    RENTAL = "rental"
    PENSION = "pension"
    DISABILITY = "disability"
    CHILD_SUPPORT = "child_support"
    ALIMONY = "alimony"
    INVESTMENT = "investment"
    OTHER = "other"


class RateType(str, Enum):
    """Mortgage interest rate types."""
    VARIABLE = "variable"
    FIXED_1_YEAR = "fixed_1_year"
    FIXED_2_YEAR = "fixed_2_year"
    FIXED_3_YEAR = "fixed_3_year"
    FIXED_4_YEAR = "fixed_4_year"
    FIXED_5_YEAR = "fixed_5_year"
    FIXED_7_YEAR = "fixed_7_year"
    FIXED_10_YEAR = "fixed_10_year"


class UnderwritingDecision(str, Enum):
    """Final underwriting decisions."""
    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REFER = "refer"  # Requires senior underwriter review
    DECLINE = "decline"
    COUNTEROFFER = "counteroffer"  # Offer different terms


class FindingSeverity(str, Enum):
    """Severity levels for policy findings."""
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    FAIL = "fail"


class RiskLevel(str, Enum):
    """Overall risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# OSFI B-20 Constants
OSFI_B20_GDS_LIMIT = 0.39  # 39%
OSFI_B20_TDS_LIMIT = 0.44  # 44%
OSFI_MQR_FLOOR_RATE = 5.25  # 5.25% floor rate
OSFI_MQR_BUFFER = 2.0  # +2% buffer on contract rate

# LTV Limits
LTV_CONVENTIONAL_MAX = 0.80  # 80% for conventional
LTV_INSURED_MAX = 0.95  # 95% for insured
LTV_REFINANCE_MAX = 0.80  # 80% for refinance

# Amortization Limits
MAX_AMORTIZATION_INSURED = 25  # years
MAX_AMORTIZATION_UNINSURED = 30  # years

# Down Payment Thresholds
MIN_DOWN_PAYMENT_PERCENTAGE = 0.05  # 5%
DOWN_PAYMENT_THRESHOLD_1 = 500_000  # First threshold
DOWN_PAYMENT_THRESHOLD_2 = 1_000_000  # Second threshold (20% required)

# Income Haircuts
HAIRCUT_BONUS = 0.50  # 50% haircut
HAIRCUT_COMMISSION = 0.50  # 50% haircut
HAIRCUT_OVERTIME = 0.50  # 50% haircut
HAIRCUT_RENTAL = 0.50  # 50% offset for expenses

# Credit Score Thresholds
CREDIT_SCORE_EXCELLENT = 740
CREDIT_SCORE_GOOD = 680
CREDIT_SCORE_FAIR = 650
CREDIT_SCORE_SUBPRIME = 600
CREDIT_SCORE_MIN_INSURED = 680
CREDIT_SCORE_MIN_CONVENTIONAL = 650

# RRSP Home Buyers' Plan
HBP_MAX_PER_PERSON = 35_000  # $35,000 per person
HBP_MAX_COUPLE = 70_000  # $70,000 for couple
