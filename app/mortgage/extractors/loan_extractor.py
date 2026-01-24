"""
Loan field extractor for mortgage documents.
"""

import re
from typing import Any, Dict, Optional


def extract_loan_fields(cu_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract loan fields from Content Understanding result.
    
    Args:
        cu_result: Raw CU extraction result
        
    Returns:
        Dictionary with normalized loan fields
    """
    fields = cu_result.get("fields", {})
    
    result = {}
    
    # Loan amount
    if "RequestedLoanAmount" in fields:
        result["loanAmount"] = _parse_currency(_extract_value(fields["RequestedLoanAmount"]))
    
    # Amortization
    if "RequestedAmortization" in fields:
        result["amortizationYears"] = _parse_years(_extract_value(fields["RequestedAmortization"]))
    
    # Interest rate
    if "InterestRate" in fields:
        result["interestRate"] = _parse_percentage(_extract_value(fields["InterestRate"]))
    
    # Down payment amount
    if "DownPaymentAmount" in fields:
        result["downPaymentAmount"] = _parse_currency(_extract_value(fields["DownPaymentAmount"]))
    
    # Down payment percentage
    if "DownPaymentPercentage" in fields:
        result["downPaymentPercentage"] = _parse_percentage(_extract_value(fields["DownPaymentPercentage"]))
    
    # Rate term
    if "RateTerm" in fields:
        result["rateTerm"] = _extract_value(fields["RateTerm"])
    
    # Payment frequency
    if "PaymentFrequency" in fields:
        result["paymentFrequency"] = _extract_value(fields["PaymentFrequency"])
    
    # Monthly payment
    if "MortgagePaymentAmount" in fields:
        result["mortgagePayment"] = _parse_currency(_extract_value(fields["MortgagePaymentAmount"]))
    
    return result


def _extract_value(field_data: Any) -> Any:
    """Extract value from field data structure."""
    if isinstance(field_data, dict):
        return field_data.get("value", field_data.get("content"))
    return field_data


def _parse_currency(value: Any) -> Optional[float]:
    """Parse currency string to float."""
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        cleaned = re.sub(r'[$,\s]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None


def _parse_percentage(value: Any) -> Optional[float]:
    """
    Parse percentage string to float.
    
    Handles: "5.25%", "5.25 percent", 5.25, 0.0525
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        # If already a decimal < 1, convert to percentage
        if 0 < value < 1:
            return value * 100
        return float(value)
    
    if isinstance(value, str):
        # Remove % sign and "percent" text
        cleaned = re.sub(r'[%\s]|percent', '', value.lower())
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None


def _parse_years(value: Any) -> Optional[int]:
    """
    Parse years from string.
    
    Handles: "25 years", "25", 25
    """
    if value is None:
        return None
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        # Extract number from string
        match = re.search(r'\d+', value)
        if match:
            return int(match.group())
    
    return None
