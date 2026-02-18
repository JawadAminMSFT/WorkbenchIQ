"""
Video Content Extractor for Automotive Claims

Extracts structured video information from Azure Content Understanding
video analysis results, including segments, keyframes, and transcripts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Keyframe:
    """A keyframe extracted from video analysis."""
    timestamp: Any  # e.g., "0:00:05" or 15.5 (float seconds)
    url: Optional[str] = None  # URL to keyframe image if available
    frame_url: Optional[str] = None  # Alternative name for URL
    description: Optional[str] = None
    segment_id: Optional[str] = None
    is_impact_frame: bool = False
    objects_detected: Optional[List[str]] = None  # List of detected objects


@dataclass
class SignificantSound:
    """A significant sound detected in the video."""
    timestamp: str
    sound_type: str  # Impact, Braking, Horn, Glass Breaking, etc.
    confidence: float = 0.0


@dataclass
class TrafficSignal:
    """A traffic signal visible in the video."""
    signal_type: str  # Traffic Light, Stop Sign, Yield, etc.
    state: Optional[str] = None  # Red, Yellow, Green
    timestamp: Optional[str] = None


@dataclass
class VehicleInVideo:
    """A vehicle identified in the video."""
    vehicle_id: str
    vehicle_type: Optional[str] = None  # Sedan, SUV, Truck, etc.
    color: Optional[str] = None
    role: Optional[str] = None  # Subject Vehicle, Other Party, Witness, Parked
    license_plate: Optional[str] = None


@dataclass
class VideoSegment:
    """A logical segment of the video."""
    segment_id: str
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[str] = None
    label: Optional[str] = None  # Pre-Incident, Impact, Post-Incident
    description: Optional[str] = None
    transcript: Optional[str] = None
    keyframes: List[Keyframe] = field(default_factory=list)
    event_type: Optional[str] = None  # normal_driving, collision, braking, etc.
    confidence: Optional[float] = None  # 0.0 to 1.0


@dataclass
class VideoData:
    """Complete video analysis data."""
    # Metadata
    duration: Optional[str] = None
    video_source: Optional[str] = None  # Dashcam, Surveillance, Phone, Body Camera
    video_quality: Optional[str] = None  # HD, SD, Low
    
    # Incident detection
    incident_detected: bool = False
    impact_timestamp: Optional[str] = None
    incident_type: Optional[str] = None  # Rear-end, T-bone, Sideswipe, etc.
    
    # Content
    segments: List[VideoSegment] = field(default_factory=list)
    keyframes: List[Keyframe] = field(default_factory=list)
    transcript: Optional[str] = None
    
    # Detected elements
    vehicles: List[VehicleInVideo] = field(default_factory=list)
    significant_sounds: List[SignificantSound] = field(default_factory=list)
    traffic_signals: List[TrafficSignal] = field(default_factory=list)
    
    # Movement and conditions
    estimated_speed: Optional[str] = None
    movement_pattern: Optional[str] = None  # Straight, Turning, Lane Change, etc.
    traffic_conditions: Optional[str] = None  # Light, Moderate, Heavy, Stopped
    weather_visible: Optional[str] = None  # Clear, Rain, Snow, Fog
    time_of_day: Optional[str] = None  # Daytime, Dusk, Dawn, Night
    
    # Liability indicators
    lane_markings_visible: bool = False
    right_of_way_violation: bool = False
    
    # Raw data
    raw_fields: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class VideoExtractor:
    """
    Extracts video analysis data from CU results.
    
    Parses the Azure Content Understanding response for video analysis
    and extracts structured data including segments, keyframes, and transcript.
    """
    
    def extract(self, cu_result: Dict[str, Any]) -> VideoData:
        """
        Extract video data from a CU video analysis result.
        
        Args:
            cu_result: Raw result from Content Understanding API
            
        Returns:
            VideoData with all extracted information
        """
        raw_fields = self._get_fields(cu_result)
        confidence_scores = self._get_confidence_scores(cu_result)
        
        # Extract complex structures
        segments = self._extract_segments(cu_result, raw_fields)
        keyframes = self._extract_keyframes(cu_result, raw_fields)
        transcript = self._extract_transcript(cu_result, raw_fields)
        vehicles = self._extract_vehicles(raw_fields)
        sounds = self._extract_sounds(raw_fields)
        signals = self._extract_traffic_signals(raw_fields)
        
        return VideoData(
            duration=self._get_string(raw_fields, "VideoDuration"),
            video_source=self._get_string(raw_fields, "VideoSource"),
            video_quality=self._get_string(raw_fields, "VideoQuality"),
            incident_detected=self._get_bool(raw_fields, "IncidentDetected"),
            impact_timestamp=self._get_string(raw_fields, "ImpactTimestamp"),
            incident_type=self._get_string(raw_fields, "IncidentType"),
            segments=segments,
            keyframes=keyframes,
            transcript=transcript,
            vehicles=vehicles,
            significant_sounds=sounds,
            traffic_signals=signals,
            estimated_speed=self._get_string(raw_fields, "EstimatedSpeed"),
            movement_pattern=self._get_string(raw_fields, "MovementPattern"),
            traffic_conditions=self._get_string(raw_fields, "TrafficConditions"),
            weather_visible=self._get_string(raw_fields, "WeatherVisible"),
            time_of_day=self._get_string(raw_fields, "TimeOfDay"),
            lane_markings_visible=self._get_bool(raw_fields, "LaneMarkingsVisible"),
            right_of_way_violation=self._get_bool(raw_fields, "RightOfWayViolation"),
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
        
        return {}
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field values from CU format to simple values."""
        normalized = {}
        for key, field_data in fields.items():
            if isinstance(field_data, dict):
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
        """Get a string value from fields."""
        value = fields.get(key)
        return str(value) if value is not None else None
    
    def _get_bool(self, fields: Dict[str, Any], key: str) -> bool:
        """Get a boolean value from fields."""
        value = fields.get(key)
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)
    
    def _extract_segments(self, cu_result: Dict[str, Any], fields: Dict[str, Any]) -> List[VideoSegment]:
        """Extract video segments from the result."""
        segments = []
        
        # First check fields for VideoSegments
        segments_data = fields.get("VideoSegments", [])
        if isinstance(segments_data, list):
            for idx, seg in enumerate(segments_data):
                if isinstance(seg, dict):
                    segments.append(VideoSegment(
                        segment_id=str(seg.get("id", idx)),
                        start_time=seg.get("startTime") or seg.get("start_time", "0:00:00"),
                        end_time=seg.get("endTime") or seg.get("end_time"),
                        duration=seg.get("duration"),
                        label=seg.get("label"),
                        description=seg.get("description"),
                        transcript=seg.get("transcript") or seg.get("speech"),
                        event_type=seg.get("event_type") or seg.get("eventType"),
                        confidence=seg.get("confidence"),
                    ))
        
        # Check result.segments (alternative structure)
        result = cu_result.get("result", {})
        if not segments and result.get("segments"):
            result_segments = result.get("segments", [])
            for idx, seg in enumerate(result_segments):
                if isinstance(seg, dict):
                    segments.append(VideoSegment(
                        segment_id=str(seg.get("id", idx)),
                        start_time=str(seg.get("startTime") or seg.get("start_time", 0)),
                        end_time=str(seg.get("endTime") or seg.get("end_time", 0)),
                        duration=seg.get("duration"),
                        label=seg.get("label"),
                        description=seg.get("description"),
                        transcript=seg.get("transcript") or seg.get("speech"),
                        event_type=seg.get("event_type") or seg.get("eventType"),
                        confidence=seg.get("confidence"),
                    ))
        
        # Also check CU result structure for segments
        if not segments:
            result = cu_result.get("result", {})
            contents = result.get("contents", [])
            for content in contents:
                if content.get("kind") == "audioVisual":
                    content_segments = content.get("segments", [])
                    for idx, seg in enumerate(content_segments):
                        kf_list = []
                        for kf in seg.get("keyframes", []):
                            kf_list.append(Keyframe(
                                timestamp=kf.get("timestamp", "0:00:00"),
                                url=kf.get("url"),
                                description=kf.get("description"),
                                segment_id=str(seg.get("id", idx)),
                            ))
                        
                        segments.append(VideoSegment(
                            segment_id=str(seg.get("id", idx)),
                            start_time=seg.get("startTime", "0:00:00"),
                            end_time=seg.get("endTime"),
                            duration=seg.get("duration"),
                            label=seg.get("label"),
                            description=seg.get("description") or seg.get("summary"),
                            transcript=seg.get("speech") or seg.get("transcript"),
                            keyframes=kf_list,
                        ))
        
        return segments
    
    def _extract_keyframes(self, cu_result: Dict[str, Any], fields: Dict[str, Any]) -> List[Keyframe]:
        """Extract keyframes from the result."""
        keyframes = []
        
        # Check CU result structure
        result = cu_result.get("result", {})
        
        # Check result.keyframes (test fixture format)
        if result.get("keyframes"):
            for kf in result.get("keyframes", []):
                keyframes.append(Keyframe(
                    timestamp=kf.get("timestamp") or kf.get("time", 0.0),
                    url=kf.get("url") or kf.get("imageUrl"),
                    description=kf.get("description") or kf.get("caption"),
                    objects_detected=kf.get("objects_detected"),
                ))
        
        contents = result.get("contents", [])
        
        for content in contents:
            if content.get("kind") == "audioVisual":
                # Top-level keyframes
                for kf in content.get("keyframes", []):
                    keyframes.append(Keyframe(
                        timestamp=kf.get("timestamp") or kf.get("time", "0:00:00"),
                        url=kf.get("url") or kf.get("imageUrl"),
                        description=kf.get("description") or kf.get("caption"),
                    ))
                
                # Keyframes within segments
                for seg in content.get("segments", []):
                    for kf in seg.get("keyframes", []):
                        keyframes.append(Keyframe(
                            timestamp=kf.get("timestamp") or kf.get("time", "0:00:00"),
                            url=kf.get("url") or kf.get("imageUrl"),
                            description=kf.get("description") or kf.get("caption"),
                            segment_id=str(seg.get("id")),
                        ))
        
        # Legacy format
        if not keyframes:
            for kf in cu_result.get("keyframes", []):
                keyframes.append(Keyframe(
                    timestamp=kf.get("timestamp", "0:00:00"),
                    url=kf.get("url"),
                    description=kf.get("description"),
                ))
        
        return keyframes
    
    def _extract_transcript(self, cu_result: Dict[str, Any], fields: Dict[str, Any]) -> Optional[str]:
        """Extract transcript from the result."""
        # Check fields first
        if fields.get("Transcript"):
            return str(fields["Transcript"])
        
        # Check CU result structure
        transcript_parts = []
        result = cu_result.get("result", {})
        contents = result.get("contents", [])
        
        for content in contents:
            if content.get("kind") == "audioVisual":
                if content.get("transcript"):
                    transcript_parts.append(content["transcript"])
                if content.get("markdown"):
                    transcript_parts.append(content["markdown"])
                
                for seg in content.get("segments", []):
                    speech = seg.get("speech") or seg.get("transcript", "")
                    if speech:
                        timestamp = seg.get("startTime", "")
                        if timestamp:
                            transcript_parts.append(f"[{timestamp}] {speech}")
                        else:
                            transcript_parts.append(speech)
        
        return "\n".join(transcript_parts) if transcript_parts else None
    
    def _extract_vehicles(self, fields: Dict[str, Any]) -> List[VehicleInVideo]:
        """Extract identified vehicles from fields."""
        vehicles = []
        vehicles_data = fields.get("VehiclesIdentified", [])
        
        if isinstance(vehicles_data, list):
            for idx, veh in enumerate(vehicles_data):
                if isinstance(veh, dict):
                    vehicles.append(VehicleInVideo(
                        vehicle_id=str(veh.get("vehicleId", f"vehicle_{idx}")),
                        vehicle_type=veh.get("type"),
                        color=veh.get("color"),
                        role=veh.get("role"),
                        license_plate=veh.get("licensePlate"),
                    ))
        
        return vehicles
    
    def _extract_sounds(self, fields: Dict[str, Any]) -> List[SignificantSound]:
        """Extract significant sounds from fields."""
        sounds = []
        sounds_data = fields.get("SignificantSounds", [])
        
        if isinstance(sounds_data, list):
            for sound in sounds_data:
                if isinstance(sound, dict):
                    sounds.append(SignificantSound(
                        timestamp=sound.get("timestamp", "0:00:00"),
                        sound_type=sound.get("soundType", "Unknown"),
                        confidence=float(sound.get("confidence", 0.0)),
                    ))
        
        return sounds
    
    def _extract_traffic_signals(self, fields: Dict[str, Any]) -> List[TrafficSignal]:
        """Extract traffic signals from fields."""
        signals = []
        signals_data = fields.get("TrafficSignalsVisible", [])
        
        if isinstance(signals_data, list):
            for sig in signals_data:
                if isinstance(sig, dict):
                    signals.append(TrafficSignal(
                        signal_type=sig.get("type", "Unknown"),
                        state=sig.get("state"),
                        timestamp=sig.get("timestamp"),
                    ))
        
        return signals


# Module-level convenience function
def extract_video_data(cu_result: Dict[str, Any]) -> VideoData:
    """
    Extract video data from a CU video analysis result.
    
    Convenience function that creates an extractor and extracts data.
    
    Args:
        cu_result: Raw result from Content Understanding API
        
    Returns:
        VideoData with all extracted information
    """
    extractor = VideoExtractor()
    return extractor.extract(cu_result)


__all__ = [
    "VideoExtractor",
    "extract_video_data",
    "VideoData",
    "VideoSegment",
    "Keyframe",
    "VehicleInVideo",
    "SignificantSound",
    "TrafficSignal",
]
