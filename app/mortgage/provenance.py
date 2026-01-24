"""
Provenance tracker for mortgage field extraction.

Tracks the source and attribution of all extracted fields.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class FieldSource:
    """Source attribution for an extracted field."""
    doc_id: str
    doc_type: str
    page: int
    value: Any
    confidence: float = 0.0
    region: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConflictResolution:
    """Resolution record for a field conflict."""
    field_name: str
    winner_doc_id: str
    loser_doc_ids: List[str]
    note: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ProvenanceTracker:
    """
    Tracks provenance of extracted mortgage fields.
    
    Maintains a record of:
    - Which document each field value came from
    - Page and region within the document
    - Confidence scores from extraction
    - Conflict resolutions when multiple sources disagree
    """
    
    def __init__(self):
        """Initialize provenance tracker."""
        self._field_sources: Dict[str, List[Dict[str, Any]]] = {}
        self._resolutions: Dict[str, ConflictResolution] = {}
    
    def track_field(
        self,
        field_name: str,
        value: Any,
        doc_id: str,
        page: int,
        region: Optional[Dict[str, Any]] = None,
        doc_type: str = "unknown",
        confidence: float = 0.0
    ) -> None:
        """
        Track a field extraction source.
        
        Args:
            field_name: Name of the field
            value: Extracted value
            doc_id: Source document identifier
            page: Page number (1-indexed)
            region: Bounding region {x, y, width, height}
            doc_type: Type of document (t4, pay_stub, etc.)
            confidence: Extraction confidence score
        """
        if field_name not in self._field_sources:
            self._field_sources[field_name] = []
        
        self._field_sources[field_name].append({
            "doc_id": doc_id,
            "doc_type": doc_type,
            "page": page,
            "value": value,
            "confidence": confidence,
            "region": region or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_field_sources(self, field_name: str) -> List[Dict[str, Any]]:
        """
        Get all sources for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            List of source records
        """
        return self._field_sources.get(field_name, [])
    
    def resolve_conflict(
        self,
        field_name: str,
        winner_doc_id: str,
        note: str
    ) -> None:
        """
        Record a conflict resolution.
        
        Args:
            field_name: Name of the conflicting field
            winner_doc_id: Document ID of the winning value
            note: Explanation for the resolution
        """
        sources = self.get_field_sources(field_name)
        loser_ids = [s["doc_id"] for s in sources if s["doc_id"] != winner_doc_id]
        
        self._resolutions[field_name] = ConflictResolution(
            field_name=field_name,
            winner_doc_id=winner_doc_id,
            loser_doc_ids=loser_ids,
            note=note
        )
    
    def get_resolution(self, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the conflict resolution for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Resolution record or None
        """
        resolution = self._resolutions.get(field_name)
        if resolution:
            return {
                "field_name": resolution.field_name,
                "winner_doc_id": resolution.winner_doc_id,
                "loser_doc_ids": resolution.loser_doc_ids,
                "note": resolution.note,
                "timestamp": resolution.timestamp
            }
        return None
    
    def get_all_resolutions(self) -> Dict[str, Dict[str, Any]]:
        """Get all conflict resolutions."""
        return {
            name: self.get_resolution(name)
            for name in self._resolutions
        }
    
    def export_provenance(self) -> Dict[str, Any]:
        """
        Export complete provenance record.
        
        Returns:
            Dictionary with all field sources and resolutions
        """
        return {
            "field_sources": self._field_sources,
            "resolutions": {
                name: self.get_resolution(name)
                for name in self._resolutions
            },
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def has_conflicts(self, field_name: str) -> bool:
        """
        Check if a field has conflicting values from multiple sources.
        
        Args:
            field_name: Name of the field
            
        Returns:
            True if multiple sources with different values exist
        """
        sources = self.get_field_sources(field_name)
        if len(sources) <= 1:
            return False
        
        values = set()
        for source in sources:
            val = source.get("value")
            # Convert to comparable type
            if isinstance(val, (int, float)):
                values.add(round(val, 2))
            else:
                values.add(val)
        
        return len(values) > 1
