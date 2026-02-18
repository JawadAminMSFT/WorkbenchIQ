"""
Property field extractor for mortgage documents.
"""

import re
from typing import Any, Dict, Optional


def extract_property_fields(cu_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract property fields from Content Understanding result.
    
    Args:
        cu_result: Raw CU extraction result
        
    Returns:
        Dictionary with normalized property fields
    """
    fields = cu_result.get("fields", {})
    
    result = {}
    
    # Property address
    if "PropertyAddress" in fields:
        result["address"] = _extract_value(fields["PropertyAddress"])
    
    # Property type
    if "PropertyType" in fields:
        result["propertyType"] = _extract_value(fields["PropertyType"])
    
    # Purchase price
    if "PurchasePrice" in fields:
        result["purchasePrice"] = _parse_currency(_extract_value(fields["PurchasePrice"]))
    
    # Appraised value
    if "AppraisedValue" in fields:
        result["appraisedValue"] = _parse_currency(_extract_value(fields["AppraisedValue"]))
    
    # Property taxes (annual)
    if "PropertyTaxesAnnual" in fields:
        result["propertyTaxesAnnual"] = _parse_currency(_extract_value(fields["PropertyTaxesAnnual"]))
    
    # Condo fees (monthly)
    if "CondoFeesMonthly" in fields:
        result["condoFeesMonthly"] = _parse_currency(_extract_value(fields["CondoFeesMonthly"]))
    
    # Heating costs (monthly)
    if "HeatingCostMonthly" in fields:
        result["heatingCostMonthly"] = _parse_currency(_extract_value(fields["HeatingCostMonthly"]))
    
    # Year built
    if "YearBuilt" in fields:
        result["yearBuilt"] = _extract_value(fields["YearBuilt"])
    
    # Living area
    if "LivingArea" in fields:
        result["livingArea"] = _parse_number(_extract_value(fields["LivingArea"]))
    
    # Lot size
    if "LotSize" in fields:
        result["lotSize"] = _extract_value(fields["LotSize"])
    
    # Appraisal info
    if "AppraisalDate" in fields:
        result["appraisalDate"] = _extract_value(fields["AppraisalDate"])
    if "AppraiserName" in fields:
        result["appraiserName"] = _extract_value(fields["AppraiserName"])
    
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


def _parse_number(value: Any) -> Optional[float]:
    """Parse number string to float."""
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Extract first number from string
        match = re.search(r'[\d,]+\.?\d*', value.replace(',', ''))
        if match:
            try:
                return float(match.group().replace(',', ''))
            except ValueError:
                return None
    
    return None
