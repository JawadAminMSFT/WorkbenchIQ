"""
Document processor for Canadian mortgage underwriting.

Handles extraction, validation, and normalization of mortgage document fields.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class FieldProvenance:
    """Provenance information for an extracted field."""
    page: int
    confidence: float
    polygon: Optional[list] = None
    bounding_region: Optional[dict] = None
    source_document: Optional[str] = None


def extract_field_provenance(
    cu_response: Dict[str, Any],
    field_name: str
) -> Dict[str, Any]:
    """
    Extract provenance information from Content Understanding response.
    
    Args:
        cu_response: Response from Azure Content Understanding
        field_name: Name of the field to extract provenance for
        
    Returns:
        Dictionary with provenance info (page, confidence, polygon/boundingRegion)
    """
    provenance = {
        "page": 1,  # Default to page 1
        "confidence": 0.0,
    }
    
    fields = cu_response.get("fields", {})
    field_data = fields.get(field_name, {})
    
    if not field_data:
        return provenance
    
    # Extract confidence
    provenance["confidence"] = field_data.get("confidence", 0.0)
    
    # Extract bounding region
    bounding_region = field_data.get("boundingRegion", {})
    if bounding_region:
        provenance["page"] = bounding_region.get("page", 1)
        provenance["boundingRegion"] = bounding_region
        
        if "polygon" in bounding_region:
            provenance["polygon"] = bounding_region["polygon"]
    
    # Alternative: check for separate page field
    if "page" in field_data:
        provenance["page"] = field_data["page"]
    
    return provenance


class MortgageDocProcessor:
    """
    Processes mortgage documents and normalizes extracted fields.
    
    Handles:
    - Field normalization (currency, dates, percentages)
    - Multi-document field aggregation
    - Validation of extracted values
    """
    
    # Fields expected from T4 documents
    T4_FIELDS = [
        "EmployerName",
        "EmployerAddress",
        "EmployeeFirstName",
        "EmployeeLastName",
        "SocialInsuranceNumber",
        "EmploymentIncome",
        "IncomeTaxDeducted",
        "TaxYear",
    ]
    
    # Fields expected from pay stubs
    PAYSTUB_FIELDS = [
        "EmployerName",
        "EmployeeName",
        "PayPeriod",
        "PayDate",
        "GrossEarnings",
        "NetPay",
        "YTDGross",
        "YTDNet",
        "HoursWorked",
    ]
    
    # Fields expected from employment letters
    EMPLOYMENT_LETTER_FIELDS = [
        "EmployerName",
        "EmployeeName",
        "Position",
        "EmploymentType",
        "StartDate",
        "AnnualSalary",
        "HourlyRate",
        "HoursPerWeek",
    ]
    
    # Fields expected from appraisals
    APPRAISAL_FIELDS = [
        "PropertyAddress",
        "EstimatedValue",
        "AppraisalDate",
        "AppraiserName",
        "PropertyType",
        "LotSize",
        "BuildingSize",
        "YearBuilt",
    ]
    
    def __init__(self):
        """Initialize processor."""
        self._field_extractors = {
            't4': self._extract_t4_fields,
            'pay_stub': self._extract_paystub_fields,
            'employment_letter': self._extract_employment_letter_fields,
            'appraisal_report': self._extract_appraisal_fields,
        }
        self._cu_client = None
    
    def _call_content_understanding(self, doc_info: Dict[str, Any], settings: Any) -> Dict[str, Any]:
        """
        Call Azure Content Understanding to analyze document.
        
        Args:
            doc_info: Document information including file_path
            settings: Application settings
            
        Returns:
            Content Understanding extraction result
        """
        # In production, this would call the actual CU API
        # For now, return empty result (will be mocked in tests)
        return {"fields": {}}
    
    def process_document(
        self,
        doc_info: Dict[str, Any],
        settings: Any
    ) -> Dict[str, Any]:
        """
        Process a single mortgage document.
        
        Args:
            doc_info: Document info with file_path and doc_type
            settings: Application settings
            
        Returns:
            Processed extraction results
        """
        # Get Content Understanding results
        cu_result = self._call_content_understanding(doc_info, settings)
        
        doc_type = doc_info.get("doc_type", "other")
        filename = doc_info.get("file_path", "unknown")
        
        # Process using type-specific extractor
        return self.process_cu_result(cu_result, doc_type, filename)
    
    def process_package(
        self,
        documents: list[Dict[str, Any]],
        settings: Any
    ) -> list[Dict[str, Any]]:
        """
        Process multiple documents in a mortgage package.
        
        Args:
            documents: List of document info dicts
            settings: Application settings
            
        Returns:
            List of processed extraction results
        """
        results = []
        for doc_info in documents:
            result = self.process_document(doc_info, settings)
            results.append(result)
        return results
    
    def process_cu_result(
        self,
        cu_response: Dict[str, Any],
        doc_type: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Process extracted document data and normalize fields.
        
        Args:
            cu_response: Raw response from Content Understanding
            doc_type: Document type
            filename: Original filename
            
        Returns:
            Processed document with normalized fields and provenance
        """
        extractor = self._field_extractors.get(doc_type, self._extract_generic_fields)
        
        extracted = extractor(cu_response)
        
        # Add provenance for each field
        for field_name in extracted.get("fields", {}):
            provenance = extract_field_provenance(cu_response, field_name)
            extracted["fields"][field_name]["provenance"] = provenance
        
        # Add metadata
        extracted["metadata"] = {
            "doc_type": doc_type,
            "filename": filename,
            "source": "azure_content_understanding",
        }
        
        return extracted
    
    def _extract_t4_fields(self, cu_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize T4 fields."""
        fields = cu_response.get("fields", {})
        
        return {
            "doc_type": "t4",
            "fields": {
                name: self._normalize_field(fields.get(name, {}))
                for name in self.T4_FIELDS
                if name in fields
            }
        }
    
    def _extract_paystub_fields(self, cu_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize pay stub fields."""
        fields = cu_response.get("fields", {})
        
        return {
            "doc_type": "pay_stub",
            "fields": {
                name: self._normalize_field(fields.get(name, {}))
                for name in self.PAYSTUB_FIELDS
                if name in fields
            }
        }
    
    def _extract_employment_letter_fields(self, cu_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize employment letter fields."""
        fields = cu_response.get("fields", {})
        
        return {
            "doc_type": "employment_letter",
            "fields": {
                name: self._normalize_field(fields.get(name, {}))
                for name in self.EMPLOYMENT_LETTER_FIELDS
                if name in fields
            }
        }
    
    def _extract_appraisal_fields(self, cu_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize appraisal fields."""
        fields = cu_response.get("fields", {})
        
        return {
            "doc_type": "appraisal_report",
            "fields": {
                name: self._normalize_field(fields.get(name, {}))
                for name in self.APPRAISAL_FIELDS
                if name in fields
            }
        }
    
    def _extract_generic_fields(self, cu_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all fields without specific normalization."""
        fields = cu_response.get("fields", {})
        
        return {
            "doc_type": "other",
            "fields": {
                name: self._normalize_field(field_data)
                for name, field_data in fields.items()
            }
        }
    
    def _normalize_field(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single field value.
        
        Handles currency, dates, percentages, etc.
        """
        if not field_data:
            return {"value": None, "confidence": 0.0}
        
        value = field_data.get("value", field_data.get("content"))
        confidence = field_data.get("confidence", 0.0)
        
        # Try to normalize currency values
        if isinstance(value, str):
            value = self._normalize_currency(value)
        
        return {
            "value": value,
            "confidence": confidence,
            "raw": field_data.get("content", str(value)),
        }
    
    def _normalize_currency(self, value: str) -> Any:
        """Normalize currency string to float if possible."""
        if not isinstance(value, str):
            return value
        
        # Remove common currency formatting
        cleaned = value.replace('$', '').replace(',', '').replace(' ', '').strip()
        
        try:
            return float(cleaned)
        except ValueError:
            return value
