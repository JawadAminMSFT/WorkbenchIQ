"""
Result Aggregator for Automotive Claims

Aggregates and reconciles data extracted from multiple media sources
(documents, images, videos) for a single claim, with conflict resolution
and overall damage severity calculation.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from ..claims import (
    SEVERITY_MINIMAL,
    SEVERITY_MINOR,
    SEVERITY_MODERATE,
    SEVERITY_HEAVY,
    SEVERITY_TOTAL_LOSS,
)
from ..utils import setup_logging
from . import MEDIA_TYPE_DOCUMENT, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO
from .processor import ProcessingResult, ProcessingStatus
from .extractors import DocumentFields, DamageArea, VideoData

logger = setup_logging()


class ConfidenceLevel(IntEnum):
    """Confidence levels for extracted data."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class SourceAttribution:
    """Attribution to the source of a data field."""
    media_type: str
    file_id: str
    filename: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    raw_value: Any = None


@dataclass
class AggregatedField:
    """A field value with source attribution."""
    value: Any
    sources: List[SourceAttribution] = field(default_factory=list)
    conflict: bool = False
    conflicting_values: List[Tuple[Any, SourceAttribution]] = field(default_factory=list)


@dataclass
class VehicleSummary:
    """Aggregated vehicle information from all sources."""
    vin: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    make: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    model: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    year: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    color: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    license_plate: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))


@dataclass
class DamageSummary:
    """Aggregated damage information from all sources."""
    overall_severity: str
    severity_score: float  # 0.0 to 1.0
    total_estimated_cost: Optional[float] = None
    damaged_components: Set[str] = field(default_factory=set)
    damage_areas: List[DamageArea] = field(default_factory=list)
    all_severities: Dict[str, List[str]] = field(default_factory=dict)  # source -> [severities]


@dataclass
class IncidentSummary:
    """Aggregated incident information from all sources."""
    date: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    time: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    location: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    description: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    weather_conditions: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))
    fault_determination: AggregatedField = field(default_factory=lambda: AggregatedField(value=None))


@dataclass
class AggregatedResult:
    """Aggregated result from all media sources for a claim."""
    claim_id: Optional[str]
    vehicle: VehicleSummary
    damage: DamageSummary
    incident: IncidentSummary
    repair_estimate: Optional[Dict[str, Any]] = None
    parties: List[Dict[str, Any]] = field(default_factory=list)
    video_segments: List[Dict[str, Any]] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    conflicts_detected: int = 0
    confidence_score: float = 0.0  # Overall confidence 0.0 to 1.0


class ResultAggregator:
    """
    Aggregates results from multiple media sources for a claim.
    
    Handles:
    - Merging fields from documents, images, and videos
    - Conflict detection and resolution
    - Source attribution for traceability
    - Overall damage severity calculation
    
    Example:
        aggregator = ResultAggregator()
        combined = aggregator.aggregate(processing_results)
    """
    
    # Severity ranking for comparison
    SEVERITY_RANK = {
        SEVERITY_MINIMAL: 0,
        SEVERITY_MINOR: 1,
        SEVERITY_MODERATE: 2,
        SEVERITY_HEAVY: 3,
        SEVERITY_TOTAL_LOSS: 4,
    }
    
    # Reverse mapping
    RANK_TO_SEVERITY = {v: k for k, v in SEVERITY_RANK.items()}
    
    def aggregate(
        self,
        results: List[ProcessingResult],
        claim_id: Optional[str] = None,
    ) -> AggregatedResult:
        """
        Aggregate results from multiple processing results.
        
        Args:
            results: List of processing results from different media files
            claim_id: Optional claim identifier
            
        Returns:
            AggregatedResult with merged and reconciled data
        """
        # Filter to completed results only
        completed = [r for r in results if r.status == ProcessingStatus.COMPLETED]
        
        if not completed:
            return self._empty_result(claim_id)
        
        # Separate by media type
        doc_results = [r for r in completed if r.media_type == MEDIA_TYPE_DOCUMENT]
        image_results = [r for r in completed if r.media_type == MEDIA_TYPE_IMAGE]
        video_results = [r for r in completed if r.media_type == MEDIA_TYPE_VIDEO]
        
        # Aggregate each section
        vehicle = self._aggregate_vehicle(doc_results, video_results)
        damage = self._aggregate_damage(doc_results, image_results, video_results)
        incident = self._aggregate_incident(doc_results, video_results)
        
        # Get additional data
        repair_estimate = self._get_repair_estimate(doc_results)
        parties = self._get_parties(doc_results)
        video_segments = self._get_video_segments(video_results)
        
        # Count conflicts
        conflicts = self._count_conflicts([vehicle, incident])
        
        # Calculate confidence
        confidence = self._calculate_confidence(completed, conflicts)
        
        return AggregatedResult(
            claim_id=claim_id,
            vehicle=vehicle,
            damage=damage,
            incident=incident,
            repair_estimate=repair_estimate,
            parties=parties,
            video_segments=video_segments,
            source_files=[r.filename for r in completed],
            conflicts_detected=conflicts,
            confidence_score=confidence,
        )
    
    def _aggregate_vehicle(
        self,
        doc_results: List[ProcessingResult],
        video_results: List[ProcessingResult],
    ) -> VehicleSummary:
        """Aggregate vehicle info from documents and videos."""
        vehicle = VehicleSummary()
        
        # Extract from documents
        for result in doc_results:
            if isinstance(result.extracted_data, DocumentFields):
                data = result.extracted_data
                if data.vehicle:
                    source = SourceAttribution(
                        media_type=MEDIA_TYPE_DOCUMENT,
                        file_id=result.file_id,
                        filename=result.filename,
                        confidence=ConfidenceLevel.HIGH,
                    )
                    self._update_field(vehicle, "vin", data.vehicle.vin, source)
                    self._update_field(vehicle, "make", data.vehicle.make, source)
                    self._update_field(vehicle, "model", data.vehicle.model, source)
                    self._update_field(vehicle, "year", data.vehicle.year, source)
                    self._update_field(vehicle, "color", data.vehicle.color, source)
                    self._update_field(vehicle, "license_plate", data.vehicle.license_plate, source)
        
        # Extract from videos (lower confidence, supplementary)
        for result in video_results:
            if isinstance(result.extracted_data, VideoData):
                data = result.extracted_data
                if data.vehicles_detected:
                    for vid_vehicle in data.vehicles_detected:
                        source = SourceAttribution(
                            media_type=MEDIA_TYPE_VIDEO,
                            file_id=result.file_id,
                            filename=result.filename,
                            confidence=ConfidenceLevel.MEDIUM,
                        )
                        self._update_field(vehicle, "make", vid_vehicle.make, source)
                        self._update_field(vehicle, "model", vid_vehicle.model, source)
                        self._update_field(vehicle, "color", vid_vehicle.color, source)
                        self._update_field(vehicle, "license_plate", vid_vehicle.license_plate, source)
        
        return vehicle
    
    def _aggregate_damage(
        self,
        doc_results: List[ProcessingResult],
        image_results: List[ProcessingResult],
        video_results: List[ProcessingResult],
    ) -> DamageSummary:
        """Aggregate damage info from all media types."""
        all_damage_areas: List[DamageArea] = []
        all_components: Set[str] = set()
        all_severities: Dict[str, List[str]] = {}
        total_cost: Optional[float] = None
        
        # From documents (repair estimates)
        for result in doc_results:
            if isinstance(result.extracted_data, DocumentFields):
                data = result.extracted_data
                all_severities[result.filename] = []
                
                if data.repair_estimate:
                    if data.repair_estimate.total:
                        if total_cost is None:
                            total_cost = data.repair_estimate.total
                        else:
                            # Average if multiple estimates
                            total_cost = (total_cost + data.repair_estimate.total) / 2
        
        # From images (damage areas)
        for result in image_results:
            if isinstance(result.extracted_data, list):
                areas = result.extracted_data  # List[DamageArea]
                all_severities[result.filename] = []
                
                for area in areas:
                    all_damage_areas.append(area)
                    if area.component:
                        all_components.add(area.component)
                    if area.severity:
                        all_severities[result.filename].append(area.severity)
        
        # From videos (damage detected in frames)
        for result in video_results:
            if isinstance(result.extracted_data, VideoData):
                data = result.extracted_data
                all_severities[result.filename] = []
                
                # VideoData might have incident_type which can indicate severity
                if hasattr(data, 'incident_type') and data.incident_type:
                    all_severities[result.filename].append(data.incident_type)
        
        # Calculate overall severity
        overall_severity, severity_score = self._calculate_overall_severity(all_severities)
        
        return DamageSummary(
            overall_severity=overall_severity,
            severity_score=severity_score,
            total_estimated_cost=total_cost,
            damaged_components=all_components,
            damage_areas=all_damage_areas,
            all_severities=all_severities,
        )
    
    def _aggregate_incident(
        self,
        doc_results: List[ProcessingResult],
        video_results: List[ProcessingResult],
    ) -> IncidentSummary:
        """Aggregate incident info from documents and videos."""
        incident = IncidentSummary()
        
        # From documents
        for result in doc_results:
            if isinstance(result.extracted_data, DocumentFields):
                data = result.extracted_data
                if data.incident:
                    source = SourceAttribution(
                        media_type=MEDIA_TYPE_DOCUMENT,
                        file_id=result.file_id,
                        filename=result.filename,
                        confidence=ConfidenceLevel.HIGH,
                    )
                    self._update_field(incident, "date", data.incident.date_of_loss, source)
                    self._update_field(incident, "time", data.incident.date_reported, source)
                    self._update_field(incident, "location", data.incident.location, source)
                    self._update_field(incident, "description", data.incident.description, source)
                    self._update_field(incident, "weather_conditions", data.incident.weather_conditions, source)
                    # Note: IncidentInfo doesn't have fault_determination, skip it
        
        # From videos (metadata and transcript analysis)
        for result in video_results:
            if isinstance(result.extracted_data, VideoData):
                data = result.extracted_data
                source = SourceAttribution(
                    media_type=MEDIA_TYPE_VIDEO,
                    file_id=result.file_id,
                    filename=result.filename,
                    confidence=ConfidenceLevel.MEDIUM,
                )
                if data.impact_timestamp:
                    self._update_field(incident, "time", data.impact_timestamp, source)
                if data.weather_visible:
                    self._update_field(incident, "weather_conditions", data.weather_visible, source)
        
        return incident
    
    def _update_field(
        self,
        obj: Any,
        field_name: str,
        new_value: Any,
        source: SourceAttribution,
    ) -> None:
        """Update a field value, detecting conflicts."""
        if new_value is None:
            return
        
        agg_field: AggregatedField = getattr(obj, field_name)
        
        if agg_field.value is None:
            # First value
            agg_field.value = new_value
            agg_field.sources.append(source)
        elif agg_field.value == new_value:
            # Same value, add source
            agg_field.sources.append(source)
        else:
            # Conflict detected
            if not agg_field.conflict:
                # First conflict - record original
                agg_field.conflict = True
                agg_field.conflicting_values.append((agg_field.value, agg_field.sources[0]))
            
            agg_field.conflicting_values.append((new_value, source))
            
            # Use higher confidence value
            if source.confidence > agg_field.sources[0].confidence:
                agg_field.value = new_value
                agg_field.sources = [source]
    
    def _calculate_overall_severity(
        self,
        all_severities: Dict[str, List[str]],
    ) -> Tuple[str, float]:
        """Calculate overall damage severity from all sources."""
        flat_severities = []
        for severities in all_severities.values():
            flat_severities.extend(severities)
        
        if not flat_severities:
            return SEVERITY_MINIMAL, 0.0
        
        # Get max rank among all severities
        max_rank = 0
        for sev in flat_severities:
            sev_normalized = sev.lower().replace("_", " ").replace("-", " ")
            
            for key, rank in self.SEVERITY_RANK.items():
                if key.lower() in sev_normalized or sev_normalized in key.lower():
                    max_rank = max(max_rank, rank)
                    break
        
        overall = self.RANK_TO_SEVERITY.get(max_rank, SEVERITY_MINIMAL)
        score = max_rank / 4.0  # Normalize to 0.0-1.0
        
        return overall, score
    
    def _get_repair_estimate(
        self,
        doc_results: List[ProcessingResult],
    ) -> Optional[Dict[str, Any]]:
        """Get repair estimate from document results."""
        for result in doc_results:
            if isinstance(result.extracted_data, DocumentFields):
                data = result.extracted_data
                if data.repair_estimate:
                    return {
                        "total_amount": data.repair_estimate.total,
                        "labor_cost": data.repair_estimate.labor_cost,
                        "parts_cost": data.repair_estimate.parts_cost,
                        "deductible": data.repair_estimate.deductible,
                        "line_items_count": len(data.repair_estimate.line_items),
                    }
        return None
    
    def _get_parties(
        self,
        doc_results: List[ProcessingResult],
    ) -> List[Dict[str, Any]]:
        """Get party information from document results."""
        parties = []
        seen_names: Set[str] = set()
        
        for result in doc_results:
            if isinstance(result.extracted_data, DocumentFields):
                data = result.extracted_data
                
                # Add claimant if present
                if data.claimant and data.claimant.name:
                    if data.claimant.name not in seen_names:
                        seen_names.add(data.claimant.name)
                        parties.append({
                            "name": data.claimant.name,
                            "role": data.claimant.role or "claimant",
                            "phone": data.claimant.phone,
                            "insurance_company": data.claimant.insurance_company,
                            "policy_number": data.claimant.policy_number,
                        })
                
                # Add other parties
                for party in data.other_parties:
                    if party.name and party.name not in seen_names:
                        seen_names.add(party.name)
                        parties.append({
                            "name": party.name,
                            "role": party.role,
                            "phone": party.phone,
                            "insurance_company": party.insurance_company,
                            "policy_number": party.policy_number,
                        })
        
        return parties
    
    def _get_video_segments(
        self,
        video_results: List[ProcessingResult],
    ) -> List[Dict[str, Any]]:
        """Get video segments from video results."""
        segments = []
        
        for result in video_results:
            if isinstance(result.extracted_data, VideoData):
                data = result.extracted_data
                for segment in data.segments:
                    segments.append({
                        "source_file": result.filename,
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "description": segment.description,
                        "event_type": segment.event_type,
                        "confidence": segment.confidence,
                    })
        
        return segments
    
    def _count_conflicts(self, summaries: List[Any]) -> int:
        """Count total conflicts across all summaries."""
        count = 0
        for summary in summaries:
            for field_name in dir(summary):
                if field_name.startswith("_"):
                    continue
                field_val = getattr(summary, field_name)
                if isinstance(field_val, AggregatedField) and field_val.conflict:
                    count += 1
        return count
    
    def _calculate_confidence(
        self,
        results: List[ProcessingResult],
        conflicts: int,
    ) -> float:
        """Calculate overall confidence score."""
        if not results:
            return 0.0
        
        # Base confidence on number and variety of sources
        media_types = set(r.media_type for r in results)
        
        base = 0.5
        
        # Bonus for multiple media types
        base += 0.1 * len(media_types)
        
        # Bonus for multiple files
        base += min(0.2, 0.05 * len(results))
        
        # Penalty for conflicts
        base -= 0.05 * conflicts
        
        return max(0.0, min(1.0, base))
    
    def _empty_result(self, claim_id: Optional[str]) -> AggregatedResult:
        """Return empty result when no data available."""
        return AggregatedResult(
            claim_id=claim_id,
            vehicle=VehicleSummary(),
            damage=DamageSummary(
                overall_severity=SEVERITY_MINIMAL,
                severity_score=0.0,
            ),
            incident=IncidentSummary(),
        )


# Convenience function
def aggregate_claim_results(
    results: List[ProcessingResult],
    claim_id: Optional[str] = None,
) -> AggregatedResult:
    """
    Aggregate results from processing claim media files.
    
    Args:
        results: List of processing results
        claim_id: Optional claim identifier
        
    Returns:
        Aggregated result with merged data
    """
    aggregator = ResultAggregator()
    return aggregator.aggregate(results, claim_id)


__all__ = [
    "ResultAggregator",
    "AggregatedResult",
    "VehicleSummary",
    "DamageSummary",
    "IncidentSummary",
    "AggregatedField",
    "SourceAttribution",
    "ConfidenceLevel",
    "aggregate_claim_results",
]
