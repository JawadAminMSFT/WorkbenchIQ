"""
Image Damage Extractor for Automotive Claims

Extracts structured damage information from Azure Content Understanding
image analysis results, including damage areas, severity, and components.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DamageArea:
    """A detected area of damage on the vehicle."""
    location: str = "Unknown"  # Front, Rear, Driver Side, Passenger Side, etc.
    damage_type: str = "Unknown"  # Dent, Scratch, Crack, Crush, Shatter, etc.
    severity: str = "Unknown"  # Minor, Moderate, Severe
    components: List[str] = field(default_factory=list)  # Bumper, Door, Fender, etc.
    component: Optional[str] = None  # Single component (alternate format)
    description: Optional[str] = None
    confidence: float = 0.0
    bounding_box: Optional[List[float]] = None  # [x, y, width, height]
    estimated_cost: Optional[float] = None  # Estimated repair cost


@dataclass
class ImageAnalysis:
    """Complete analysis result from an image."""
    vehicle_identified: bool = False
    vehicle_type: Optional[str] = None  # Sedan, SUV, Truck, etc.
    vehicle_color: Optional[str] = None
    license_plate_visible: bool = False
    license_plate_number: Optional[str] = None
    damage_detected: bool = False
    damage_areas: List[DamageArea] = field(default_factory=list)
    overall_severity: Optional[str] = None  # Minor, Moderate, Heavy, Total Loss
    estimated_repair_category: Optional[str] = None  # Cosmetic, Structural, Mechanical, Total Loss
    image_quality: Optional[str] = None  # Good, Fair, Poor
    lighting_conditions: Optional[str] = None
    angle_coverage: Optional[str] = None  # Front, Side, Rear, Close-up, Wide
    raw_fields: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class ImageExtractor:
    """
    Extracts damage information from image analysis results.
    
    Parses the Azure Content Understanding response for image analysis
    and extracts structured damage data.
    """
    
    def extract(self, cu_result: Dict[str, Any]) -> ImageAnalysis:
        """
        Extract damage information from a CU image analysis result.
        
        Args:
            cu_result: Raw result from Content Understanding API
            
        Returns:
            ImageAnalysis with all extracted data
        """
        raw_fields = self._get_fields(cu_result)
        confidence_scores = self._get_confidence_scores(cu_result)
        damage_areas = self._extract_damage_areas(raw_fields)
        
        return ImageAnalysis(
            vehicle_identified=self._get_bool(raw_fields, "VehicleIdentified"),
            vehicle_type=self._get_string(raw_fields, "VehicleType"),
            vehicle_color=self._get_string(raw_fields, "VehicleColor"),
            license_plate_visible=self._get_bool(raw_fields, "LicensePlateVisible"),
            license_plate_number=self._get_string(raw_fields, "LicensePlateNumber"),
            damage_detected=self._get_bool(raw_fields, "DamageDetected"),
            damage_areas=damage_areas,
            overall_severity=self._get_string(raw_fields, "OverallDamageSeverity"),
            estimated_repair_category=self._get_string(raw_fields, "EstimatedRepairCategory"),
            image_quality=self._get_string(raw_fields, "ImageQuality"),
            lighting_conditions=self._get_string(raw_fields, "LightingConditions"),
            angle_coverage=self._get_string(raw_fields, "AngleCoverage"),
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
                    field_data.get("valueBoolean") or
                    field_data.get("valueNumber") or
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
        
        return None
    
    def _to_snake_case(self, key: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _get_bool(self, fields: Dict[str, Any], key: str) -> bool:
        """Get a boolean value from fields, trying multiple naming conventions."""
        # Try original key
        value = fields.get(key)
        if value is None:
            # Try snake_case version
            snake_key = self._to_snake_case(key)
            value = fields.get(snake_key)
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)
    
    def _extract_damage_areas(self, fields: Dict[str, Any]) -> List[DamageArea]:
        """Extract damage areas from fields."""
        areas = []
        # Try multiple field name conventions
        damage_data = (
            fields.get("DamageAreas") or 
            fields.get("damage_areas") or
            fields.get("damageAreas") or
            []
        )
        
        if not isinstance(damage_data, list):
            return areas
        
        for item in damage_data:
            if not isinstance(item, dict):
                continue
            
            # Get components list
            components = item.get("components", [])
            if isinstance(components, str):
                components = [c.strip() for c in components.split(",")]
            
            areas.append(DamageArea(
                location=item.get("location", "Unknown"),
                damage_type=item.get("damageType") or item.get("damage_type", "Unknown"),
                severity=item.get("severity", "Unknown"),
                components=components if isinstance(components, list) else [],
                description=item.get("description"),
                confidence=float(item.get("confidence", 0.0)),
                bounding_box=item.get("boundingBox") or item.get("bounding_box"),
                component=item.get("component"),  # Single component field
            ))
        
        return areas


# Module-level convenience function
def extract_damage_areas(cu_result: Dict[str, Any]) -> List[DamageArea]:
    """
    Extract damage areas from a CU image analysis result.
    
    Convenience function that creates an extractor and extracts damage areas.
    
    Args:
        cu_result: Raw result from Content Understanding API
        
    Returns:
        List of DamageArea objects
    """
    extractor = ImageExtractor()
    analysis = extractor.extract(cu_result)
    return analysis.damage_areas


__all__ = [
    "ImageExtractor",
    "extract_damage_areas",
    "DamageArea",
    "ImageAnalysis",
]
