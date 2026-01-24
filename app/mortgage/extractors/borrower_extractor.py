"""
Borrower field extractor for mortgage documents.
"""

from typing import Any, Dict


def extract_borrower_fields(cu_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract borrower identity fields from Content Understanding result.
    
    Args:
        cu_result: Raw CU extraction result
        
    Returns:
        Dictionary with normalized borrower fields
    """
    fields = cu_result.get("fields", {})
    
    result = {}
    
    # Full name
    if "BorrowerFullName" in fields:
        result["fullName"] = _extract_value(fields["BorrowerFullName"])
    elif "BorrowerName" in fields:
        result["fullName"] = _extract_value(fields["BorrowerName"])
    
    # Date of birth
    if "BorrowerDateOfBirth" in fields:
        result["dateOfBirth"] = _extract_value(fields["BorrowerDateOfBirth"])
    elif "DateOfBirth" in fields:
        result["dateOfBirth"] = _extract_value(fields["DateOfBirth"])
    
    # SIN (redacted)
    if "BorrowerSIN" in fields:
        result["sin"] = _extract_value(fields["BorrowerSIN"])
    
    # Address
    if "BorrowerAddress" in fields:
        result["address"] = _extract_value(fields["BorrowerAddress"])
    
    # Co-borrower
    if "CoBorrowerName" in fields:
        result["coBorrowerName"] = _extract_value(fields["CoBorrowerName"])
    
    # Marital status
    if "MaritalStatus" in fields:
        result["maritalStatus"] = _extract_value(fields["MaritalStatus"])
    
    return result


def _extract_value(field_data: Any) -> Any:
    """Extract value from field data structure."""
    if isinstance(field_data, dict):
        return field_data.get("value", field_data.get("content"))
    return field_data
