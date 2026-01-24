"""
Extractors for Canadian mortgage document fields.

This package contains specialized extractors for different document types
and field categories.
"""

from app.mortgage.extractors.borrower_extractor import extract_borrower_fields
from app.mortgage.extractors.income_extractor import extract_income_fields
from app.mortgage.extractors.property_extractor import extract_property_fields
from app.mortgage.extractors.loan_extractor import extract_loan_fields
from app.mortgage.extractors.credit_extractor import extract_credit_fields

__all__ = [
    "extract_borrower_fields",
    "extract_income_fields",
    "extract_property_fields",
    "extract_loan_fields",
    "extract_credit_fields",
]
