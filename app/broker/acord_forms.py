"""
ACORD Form Templates and Field Schemas

Defines the canonical ACORD 125, ACORD 140, and SOV field schemas
used for extraction and UI rendering. Each field carries metadata
(label, type, section, required flag) so the frontend can render
editable form sections with appropriate validation.
"""

from __future__ import annotations

from typing import Any, Dict


ACORD_125_FIELDS: Dict[str, Dict[str, Any]] = {
    "InsuredName": {
        "label": "Named Insured",
        "type": "string",
        "section": "Applicant Information",
        "required": True,
    },
    "FEIN": {
        "label": "Federal Employer ID",
        "type": "string",
        "section": "Applicant Information",
        "required": True,
    },
    "BusinessPhone": {
        "label": "Business Phone",
        "type": "string",
        "section": "Applicant Information",
    },
    "BusinessAddress": {
        "label": "Mailing Address",
        "type": "string",
        "section": "Applicant Information",
        "required": True,
    },
    "BusinessType": {
        "label": "Business Entity Type",
        "type": "string",
        "section": "Applicant Information",
    },
    "YearsInBusiness": {
        "label": "Years in Business",
        "type": "number",
        "section": "Applicant Information",
    },
    "SICCode": {
        "label": "SIC Code",
        "type": "string",
        "section": "Classification",
    },
    "AnnualGrossRevenue": {
        "label": "Annual Gross Revenue",
        "type": "string",
        "section": "Financial",
    },
    "NumberOfEmployees": {
        "label": "Number of Employees",
        "type": "number",
        "section": "Financial",
    },
    "PriorCarrier": {
        "label": "Current/Prior Carrier",
        "type": "string",
        "section": "Insurance History",
    },
    "PriorPremium": {
        "label": "Prior Year Premium",
        "type": "string",
        "section": "Insurance History",
    },
    "CurrentCoverageLimits": {
        "label": "Current Coverage Limits",
        "type": "string",
        "section": "Coverage Details",
    },
    "CurrentDeductibles": {
        "label": "Current Deductibles",
        "type": "string",
        "section": "Coverage Details",
    },
    "RequestedCoverageLimits": {
        "label": "Requested Coverage Limits",
        "type": "string",
        "section": "Coverage Details",
    },
    "RequestedDeductibles": {
        "label": "Requested Deductibles",
        "type": "string",
        "section": "Coverage Details",
    },
    "CoverageModifications": {
        "label": "Coverage Modifications",
        "type": "string",
        "section": "Coverage Details",
    },
    "EffectiveDateRequested": {
        "label": "Effective Date Requested",
        "type": "date",
        "section": "Coverage",
    },
    "LinesOfBusinessRequested": {
        "label": "Lines of Business",
        "type": "array",
        "section": "Coverage",
    },
}

ACORD_140_FIELDS: Dict[str, Dict[str, Any]] = {
    # Property locations
    "PropertyAddress": {
        "label": "Property Address",
        "type": "string",
        "section": "Location",
        "required": True,
    },
    "PropertyOccupancy": {
        "label": "Occupancy Type",
        "type": "string",
        "section": "Location",
    },
    "ConstructionType": {
        "label": "Construction",
        "type": "string",
        "section": "Location",
    },
    "YearBuilt": {
        "label": "Year Built",
        "type": "number",
        "section": "Location",
    },
    "SquareFootage": {
        "label": "Square Footage",
        "type": "number",
        "section": "Location",
    },
    "BuildingValue": {
        "label": "Building Value",
        "type": "string",
        "section": "Values",
        "required": True,
    },
    "ContentsValue": {
        "label": "Contents Value",
        "type": "string",
        "section": "Values",
    },
    "BusinessInterruptionValue": {
        "label": "BI Value",
        "type": "string",
        "section": "Values",
    },
    "ProtectionClass": {
        "label": "Protection Class",
        "type": "string",
        "section": "Protection",
    },
    # Loss history
    "LossDate": {
        "label": "Date of Loss",
        "type": "date",
        "section": "Loss History",
    },
    "CauseOfLoss": {
        "label": "Cause of Loss",
        "type": "string",
        "section": "Loss History",
    },
    "LossAmountPaid": {
        "label": "Amount Paid",
        "type": "string",
        "section": "Loss History",
    },
    "LossDescription": {
        "label": "Loss Description",
        "type": "string",
        "section": "Loss History",
    },
    "LossStatus": {
        "label": "Loss Status",
        "type": "string",
        "section": "Loss History",
    },
}

SOV_FIELDS: Dict[str, Dict[str, Any]] = {
    "SiteNumber": {"label": "Site #", "type": "string"},
    "Address": {"label": "Address", "type": "string"},
    "BuildingDescription": {"label": "Description", "type": "string"},
    "TotalInsuredValue": {"label": "TIV", "type": "string"},
    "BuildingValue": {"label": "Building Value", "type": "string"},
    "ContentsValue": {"label": "Contents Value", "type": "string"},
    "BIValue": {"label": "BI Value", "type": "string"},
}

# Mapping from internal extracted field names to canonical ACORD field names
_ACORD_125_FIELD_MAP: Dict[str, str] = {
    "applicant_name": "InsuredName",
    "fein": "FEIN",
    "business_phone": "BusinessPhone",
    "mailing_address": "BusinessAddress",
    "business_type": "BusinessType",
    "years_in_business": "YearsInBusiness",
    "sic_code": "SICCode",
    "annual_gross_revenue": "AnnualGrossRevenue",
    "number_of_employees": "NumberOfEmployees",
    "prior_carrier": "PriorCarrier",
    "prior_premium": "PriorPremium",
    "current_coverage_limits": "CurrentCoverageLimits",
    "current_deductibles": "CurrentDeductibles",
    "requested_coverage_limits": "RequestedCoverageLimits",
    "requested_deductibles": "RequestedDeductibles",
    "coverage_modifications": "CoverageModifications",
    "effective_date_requested": "EffectiveDateRequested",
    "lines_of_business_requested": "LinesOfBusinessRequested",
}


def get_acord_form_template(form_type: str) -> Dict[str, Any]:
    """Return the full ACORD form template with field metadata.

    Args:
        form_type: One of "125", "140", or "sov".

    Returns:
        Dict with ``form_type``, ``title``, and ``fields`` (each field
        includes label, type, section, required flag).

    Raises:
        ValueError: If *form_type* is not recognised.
    """
    if form_type == "125":
        return {
            "form_type": "ACORD 125",
            "title": "Commercial Insurance Application",
            "fields": ACORD_125_FIELDS,
        }
    elif form_type == "140":
        return {
            "form_type": "ACORD 140",
            "title": "Property Section",
            "fields": ACORD_140_FIELDS,
        }
    elif form_type == "sov":
        return {
            "form_type": "Statement of Values",
            "title": "Schedule of Values",
            "fields": SOV_FIELDS,
        }
    else:
        raise ValueError(f"Unknown ACORD form type: {form_type}. Must be '125', '140', or 'sov'.")


def map_extracted_to_acord125(extracted: Dict[str, Any]) -> Dict[str, Any]:
    """Map internal snake_case extracted fields to canonical ACORD 125 field names.

    Args:
        extracted: Dict with snake_case keys from SubmissionGenerator extraction.

    Returns:
        Dict with canonical ACORD field names as keys.
    """
    mapped: Dict[str, Any] = {}
    for internal_key, acord_key in _ACORD_125_FIELD_MAP.items():
        if internal_key in extracted:
            mapped[acord_key] = extracted[internal_key]
    return mapped
