"""
Income field extractor for mortgage documents.
"""

import re
from typing import Any, Dict, Optional


def extract_income_fields(cu_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract income fields from Content Understanding result.
    
    Handles currency parsing and annualization of income.
    
    Args:
        cu_result: Raw CU extraction result
        
    Returns:
        Dictionary with normalized income fields
    """
    fields = cu_result.get("fields", {})
    
    result = {}
    
    # Gross annual salary
    if "GrossAnnualSalary" in fields:
        result["grossAnnualSalary"] = _parse_currency(
            _extract_value(fields["GrossAnnualSalary"])
        )
    
    # Pay period amount
    gross_pay_period = None
    if "GrossPayPeriodAmount" in fields:
        gross_pay_period = _parse_currency(
            _extract_value(fields["GrossPayPeriodAmount"])
        )
        result["grossPayPeriodAmount"] = gross_pay_period
    
    # Pay period frequency for annualization
    frequency = None
    if "PayPeriodFrequency" in fields:
        frequency = _extract_value(fields["PayPeriodFrequency"])
        result["payPeriodFrequency"] = frequency
    
    # Annualize if annual salary not provided but pay period is
    if "grossAnnualSalary" not in result and gross_pay_period and frequency:
        annualized = _annualize_income(gross_pay_period, frequency)
        if annualized:
            result["annualizedIncome"] = annualized
            result["grossAnnualSalary"] = annualized
    
    # YTD earnings
    if "YTDEarnings" in fields:
        result["ytdEarnings"] = _parse_currency(_extract_value(fields["YTDEarnings"]))
    elif "YTDGrossEarnings" in fields:
        result["ytdEarnings"] = _parse_currency(_extract_value(fields["YTDGrossEarnings"]))
    
    # Bonus income
    if "BonusAmount" in fields:
        result["bonusAmount"] = _parse_currency(_extract_value(fields["BonusAmount"]))
    
    # Commission income
    if "CommissionAmount" in fields:
        result["commissionAmount"] = _parse_currency(_extract_value(fields["CommissionAmount"]))
    
    # Overtime
    if "OvertimeAnnual" in fields:
        result["overtimeAmount"] = _parse_currency(_extract_value(fields["OvertimeAnnual"]))
    
    # T4 total income
    if "TotalIncomeFromT4" in fields:
        result["totalIncomeFromT4"] = _parse_currency(_extract_value(fields["TotalIncomeFromT4"]))
    
    # NOA total income
    if "TotalIncomeFromNOA" in fields:
        result["totalIncomeFromNOA"] = _parse_currency(_extract_value(fields["TotalIncomeFromNOA"]))
    
    # Tax year
    if "TaxYear" in fields:
        result["taxYear"] = _extract_value(fields["TaxYear"])
    
    return result


def _extract_value(field_data: Any) -> Any:
    """Extract value from field data structure."""
    if isinstance(field_data, dict):
        return field_data.get("value", field_data.get("content"))
    return field_data


def _parse_currency(value: Any) -> Optional[float]:
    """
    Parse currency string to float.
    
    Handles formats like: $125,000.00, 125000, "$125,000"
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[$,\s]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None


def _annualize_income(amount: float, frequency: str) -> Optional[float]:
    """
    Annualize income based on pay frequency.
    
    Args:
        amount: Pay period amount
        frequency: Pay frequency string
        
    Returns:
        Annualized amount
    """
    freq_lower = frequency.lower() if frequency else ""
    
    multipliers = {
        "weekly": 52,
        "bi-weekly": 26,
        "biweekly": 26,
        "semi-monthly": 24,
        "semimonthly": 24,
        "monthly": 12,
        "annual": 1,
        "annually": 1,
    }
    
    for key, multiplier in multipliers.items():
        if key in freq_lower:
            return amount * multiplier
    
    return None
