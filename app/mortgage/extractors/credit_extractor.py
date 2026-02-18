"""
Credit field extractor for mortgage documents.
"""

from typing import Any, Dict, Optional


def extract_credit_fields(cu_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract credit fields from Content Understanding result.
    
    Args:
        cu_result: Raw CU extraction result
        
    Returns:
        Dictionary with normalized credit fields
    """
    fields = cu_result.get("fields", {})
    
    result = {}
    
    # Credit score
    if "CreditScore" in fields:
        score = _extract_value(fields["CreditScore"])
        if isinstance(score, (int, float)):
            result["bureauScore"] = int(score)
        elif isinstance(score, str):
            try:
                result["bureauScore"] = int(score)
            except ValueError:
                pass
    
    # Credit bureau
    if "CreditBureau" in fields:
        bureau = _extract_value(fields["CreditBureau"])
        if bureau:
            result["bureauAgency"] = bureau.lower() if isinstance(bureau, str) else bureau
    
    # Credit report date
    if "CreditReportDate" in fields:
        result["reportDate"] = _extract_value(fields["CreditReportDate"])
    
    return result


def _extract_value(field_data: Any) -> Any:
    """Extract value from field data structure."""
    if isinstance(field_data, dict):
        return field_data.get("value", field_data.get("content"))
    return field_data
