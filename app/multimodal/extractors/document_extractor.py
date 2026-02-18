"""
Document Field Extractor for Automotive Claims

Extracts structured fields from Azure Content Understanding document analysis
results, including vehicle info, repair estimates, and party information.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PartyInfo:
    """Information about a party involved in the claim."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    drivers_license: Optional[str] = None
    insurance_company: Optional[str] = None
    policy_number: Optional[str] = None
    vehicle_info: Optional[str] = None
    role: Optional[str] = None  # Claimant, Other Party, Witness


@dataclass
class RepairLineItem:
    """Individual repair line item from estimate."""
    description: str
    part_number: Optional[str] = None
    quantity: int = 1
    unit_price: Optional[float] = None
    labor_hours: Optional[float] = None
    total_price: Optional[float] = None


@dataclass
class RepairShopInfo:
    """Information about the repair facility."""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    estimate_date: Optional[str] = None


@dataclass
class VehicleInfo:
    """Vehicle information extracted from documents."""
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    mileage: Optional[int] = None
    license_plate: Optional[str] = None


@dataclass
class IncidentInfo:
    """Incident details extracted from documents."""
    date_of_loss: Optional[str] = None
    date_reported: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    weather_conditions: Optional[str] = None
    road_conditions: Optional[str] = None
    police_report_number: Optional[str] = None


@dataclass
class RepairEstimate:
    """Repair estimate information."""
    total: Optional[float] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    deductible: Optional[float] = None
    line_items: List[RepairLineItem] = field(default_factory=list)
    repair_shop: Optional[RepairShopInfo] = None


@dataclass
class DocumentFields:
    """All fields extracted from a document."""
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    coverage_type: Optional[str] = None
    vehicle: Optional[VehicleInfo] = None
    incident: Optional[IncidentInfo] = None
    repair_estimate: Optional[RepairEstimate] = None
    claimant: Optional[PartyInfo] = None
    other_parties: List[PartyInfo] = field(default_factory=list)
    witnesses: List[PartyInfo] = field(default_factory=list)
    raw_fields: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class DocumentExtractor:
    """
    Extracts structured fields from document analysis results.
    
    Parses the Azure Content Understanding response and maps fields
    to strongly-typed dataclasses for easier processing.
    """
    
    def extract(self, cu_result: Dict[str, Any]) -> DocumentFields:
        """
        Extract all fields from a CU document analysis result.
        
        Args:
            cu_result: Raw result from Content Understanding API
            
        Returns:
            DocumentFields with all extracted data
        """
        # Get fields from result
        raw_fields = self._get_fields(cu_result)
        confidence_scores = self._get_confidence_scores(cu_result)
        
        return DocumentFields(
            claim_number=self._get_string(raw_fields, "ClaimNumber"),
            policy_number=self._get_string(raw_fields, "PolicyNumber"),
            coverage_type=self._get_string(raw_fields, "CoverageType"),
            vehicle=self._extract_vehicle(raw_fields),
            incident=self._extract_incident(raw_fields),
            repair_estimate=self._extract_repair_estimate(raw_fields),
            claimant=self._extract_party(raw_fields.get("Claimant", {})),
            other_parties=self._extract_party_list(raw_fields.get("OtherParties", [])),
            witnesses=self._extract_party_list(raw_fields.get("Witnesses", [])),
            raw_fields=raw_fields,
            confidence_scores=confidence_scores,
        )
    
    def _get_fields(self, cu_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the fields dictionary from CU result."""
        result = cu_result.get("result", {})
        
        # Try contents[].fields first (GA API format)
        contents = result.get("contents", [])
        for content in contents:
            fields = content.get("fields", {})
            if fields:
                return self._normalize_fields(fields)
        
        # Try result.fields
        if result.get("fields"):
            return self._normalize_fields(result["fields"])
        
        # Fallback to top-level fields
        if cu_result.get("fields"):
            return self._normalize_fields(cu_result["fields"])
        
        return {}
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field values from CU format to simple values."""
        normalized = {}
        for key, field_data in fields.items():
            if isinstance(field_data, dict):
                # Extract value from field object
                value = (
                    field_data.get("valueString") or
                    field_data.get("valueNumber") or
                    field_data.get("valueDate") or
                    field_data.get("valueArray") or
                    field_data.get("valueObject") or
                    field_data.get("value") or
                    field_data.get("content")
                )
                normalized[key] = value
            else:
                normalized[key] = field_data
        return normalized
    
    def _get_confidence_scores(self, cu_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract confidence scores for each field."""
        scores = {}
        result = cu_result.get("result", {})
        
        contents = result.get("contents", [])
        for content in contents:
            fields = content.get("fields", {})
            for key, field_data in fields.items():
                if isinstance(field_data, dict):
                    conf = field_data.get("confidence", 0.0)
                    if conf:
                        scores[key] = float(conf)
        
        return scores
    
    def _get_string(self, fields: Dict[str, Any], key: str) -> Optional[str]:
        """Get a string value from fields, trying multiple naming conventions."""
        # Try original key
        value = fields.get(key)
        if value is not None:
            return str(value)
        
        # Try snake_case version
        snake_key = self._to_snake_case(key)
        value = fields.get(snake_key)
        if value is not None:
            return str(value)
        
        # Try lowercase version
        value = fields.get(key.lower())
        if value is not None:
            return str(value)
        
        return None
    
    def _to_snake_case(self, key: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _get_number(self, fields: Dict[str, Any], key: str) -> Optional[float]:
        """Get a numeric value from fields, trying multiple naming conventions."""
        # Try original key
        value = fields.get(key)
        if value is None:
            # Try snake_case version
            snake_key = self._to_snake_case(key)
            value = fields.get(snake_key)
        if value is None:
            # Try lowercase version
            value = fields.get(key.lower())
        
        if value is None:
            return None
        try:
            # Handle currency strings like "$4,500.00"
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _get_int(self, fields: Dict[str, Any], key: str) -> Optional[int]:
        """Get an integer value from fields."""
        value = self._get_number(fields, key)
        return int(value) if value is not None else None
    
    def _extract_vehicle(self, fields: Dict[str, Any]) -> VehicleInfo:
        """Extract vehicle information."""
        return VehicleInfo(
            vin=self._get_string(fields, "VehicleVIN"),
            make=self._get_string(fields, "VehicleMake"),
            model=self._get_string(fields, "VehicleModel"),
            year=self._get_int(fields, "VehicleYear"),
            color=self._get_string(fields, "VehicleColor"),
            mileage=self._get_int(fields, "VehicleMileage"),
            license_plate=self._get_string(fields, "LicensePlateNumber"),
        )
    
    def _extract_incident(self, fields: Dict[str, Any]) -> IncidentInfo:
        """Extract incident information."""
        return IncidentInfo(
            date_of_loss=self._get_string(fields, "DateOfLoss"),
            date_reported=self._get_string(fields, "DateReported"),
            location=self._get_string(fields, "IncidentLocation"),
            description=self._get_string(fields, "IncidentDescription"),
            weather_conditions=self._get_string(fields, "WeatherConditions"),
            road_conditions=self._get_string(fields, "RoadConditions"),
            police_report_number=self._get_string(fields, "PoliceReportNumber"),
        )
    
    def _extract_repair_estimate(self, fields: Dict[str, Any]) -> RepairEstimate:
        """Extract repair estimate information."""
        # Extract repair shop
        shop_data = fields.get("RepairShop", {})
        repair_shop = None
        if shop_data and isinstance(shop_data, dict):
            repair_shop = RepairShopInfo(
                name=shop_data.get("name"),
                address=shop_data.get("address"),
                phone=shop_data.get("phone"),
                estimate_date=shop_data.get("estimateDate"),
            )
        
        # Extract line items
        line_items = []
        items_data = fields.get("RepairLineItems", [])
        if isinstance(items_data, list):
            for item in items_data:
                if isinstance(item, dict):
                    line_items.append(RepairLineItem(
                        description=item.get("description", ""),
                        part_number=item.get("partNumber"),
                        quantity=item.get("quantity", 1),
                        unit_price=item.get("unitPrice"),
                        labor_hours=item.get("laborHours"),
                        total_price=item.get("totalPrice"),
                    ))
        
        return RepairEstimate(
            total=self._get_number(fields, "EstimateTotal"),
            labor_cost=self._get_number(fields, "LaborCost"),
            parts_cost=self._get_number(fields, "PartsCost"),
            deductible=self._get_number(fields, "Deductible"),
            line_items=line_items,
            repair_shop=repair_shop,
        )
    
    def _extract_party(self, party_data: Any) -> Optional[PartyInfo]:
        """Extract a single party's information."""
        if not party_data or not isinstance(party_data, dict):
            return None
        
        return PartyInfo(
            name=party_data.get("name"),
            phone=party_data.get("phone"),
            email=party_data.get("email"),
            address=party_data.get("address"),
            drivers_license=party_data.get("driversLicense"),
            insurance_company=party_data.get("insuranceCompany"),
            policy_number=party_data.get("policyNumber"),
            vehicle_info=party_data.get("vehicleInfo"),
            role=party_data.get("role"),
        )
    
    def _extract_party_list(self, parties_data: Any) -> List[PartyInfo]:
        """Extract a list of parties."""
        if not parties_data or not isinstance(parties_data, list):
            return []
        
        parties = []
        for party_data in parties_data:
            party = self._extract_party(party_data)
            if party:
                parties.append(party)
        
        return parties


# Module-level convenience function
def extract_document_fields(cu_result: Dict[str, Any]) -> DocumentFields:
    """
    Extract fields from a CU document analysis result.
    
    Convenience function that creates an extractor and extracts fields.
    
    Args:
        cu_result: Raw result from Content Understanding API
        
    Returns:
        DocumentFields with all extracted data
    """
    extractor = DocumentExtractor()
    return extractor.extract(cu_result)


__all__ = [
    "DocumentExtractor",
    "extract_document_fields",
    "DocumentFields",
    "VehicleInfo",
    "IncidentInfo",
    "RepairEstimate",
    "RepairLineItem",
    "RepairShopInfo",
    "PartyInfo",
]
