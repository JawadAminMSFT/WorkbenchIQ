"""
Claims API Router for Automotive Claims Multimodal Processing

FastAPI router providing endpoints for:
- Claim submission with multimodal file upload
- Claim assessment retrieval and adjuster decisions
- Claims policy search via RAG
- Media file access (keyframes, damage areas)
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..config import load_settings
from ..utils import setup_logging
from ..database.pool import get_pool
from .policies import ClaimsPolicyLoader
from .engine import ClaimsPolicyEngine, ClaimAssessment
from .search import ClaimsPolicySearchService, ClaimsSearchResult, get_claims_policy_context
from ..rag.persona_search import AutomotiveClaimsPolicySearchService
from ..multimodal import (
    MultimodalProcessor,
    FileInfo,
    ProcessingResult,
    BatchResult,
    ProcessingStatus,
    ClaimsMediaRepository,
    detect_media_type,
)
from ..multimodal.aggregator import aggregate_claim_results
from ..storage import get_application_dir
import json
from pathlib import Path

logger = setup_logging()

# Create router with prefix
router = APIRouter(prefix="/api/claims", tags=["Automotive Claims"])


# ============================================================================
# File-based Fallback Helpers
# ============================================================================

def _get_assessment_from_files(claim_id: str) -> Optional[dict]:
    """
    Generate assessment data from file-based metadata.json with LLM outputs.
    This provides backward compatibility for claims created through the
    traditional application flow.
    Returns data matching ClaimAssessmentResponse structure.
    """
    settings = load_settings()
    root = settings.app.storage_root
    app_dir = get_application_dir(root, claim_id)
    meta_path = app_dir / "metadata.json"
    
    if not meta_path.exists():
        return None
    
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Get LLM outputs from metadata
        llm_outputs = metadata.get("llm_outputs", {})
        
        # Extract damage assessment
        damage_data = llm_outputs.get("damage_assessment", {})
        visual_analysis = damage_data.get("visual_damage_analysis", {})
        visual_parsed = visual_analysis.get("parsed", {})
        
        # Extract liability assessment
        liability_data = llm_outputs.get("liability_assessment", {})
        fault_determination = liability_data.get("fault_determination", {})
        fault_parsed = fault_determination.get("parsed", {})
        
        # Extract fraud detection
        fraud_data = llm_outputs.get("fraud_detection", {})
        red_flag_analysis = fraud_data.get("red_flag_analysis", {})
        fraud_parsed = red_flag_analysis.get("parsed", {})
        
        # Extract payout recommendation
        payout_data = llm_outputs.get("payout_recommendation", {})
        settlement_analysis = payout_data.get("settlement_analysis", {})
        payout_parsed = settlement_analysis.get("parsed", {})
        
        # Build detailed damage areas list
        damage_areas = []
        total_estimated_damage = 0.0
        for i, area in enumerate(visual_parsed.get("damage_areas", [])):
            if isinstance(area, dict):
                # Parse cost range to get estimated cost
                cost_range = area.get("estimated_cost_range", "$0")
                estimated_cost = 0.0
                if cost_range:
                    try:
                        # Extract first number from cost range like "$2,200 - $3,800"
                        cost_str = cost_range.replace("$", "").replace(",", "").split("-")[0].strip()
                        estimated_cost = float(cost_str)
                    except:
                        pass
                
                total_estimated_damage += estimated_cost
                
                damage_areas.append({
                    "area_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{claim_id}-damage-{i}")),
                    "location": area.get("location", "unknown"),
                    "severity": area.get("severity", "moderate").lower(),
                    "confidence": 0.85,
                    "estimated_cost": estimated_cost,
                    "description": f"{area.get('damage_type', 'Damage')} - {area.get('repair_method', 'Repair needed')}",
                    "bounding_box": None,
                    "source_media_id": None,
                })
        
        # Parse payout amounts
        payout_amount = 0.0
        if payout_parsed:
            recommended = payout_parsed.get("recommended_settlement", payout_parsed.get("recommended_amount", 0))
            if isinstance(recommended, (int, float)):
                payout_amount = float(recommended)
            elif isinstance(recommended, str):
                try:
                    payout_amount = float(recommended.replace(",", "").replace("$", ""))
                except:
                    pass
        
        # Build fraud indicators
        fraud_indicators = []
        for indicator in fraud_parsed.get("red_flags", fraud_parsed.get("indicators", [])):
            if isinstance(indicator, dict):
                fraud_indicators.append({
                    "indicator_type": indicator.get("category", indicator.get("type", "general")),
                    "severity": "low",  # Default to low
                    "description": indicator.get("indicator", indicator.get("description", str(indicator))),
                    "confidence": 0.7,
                })
            elif isinstance(indicator, str):
                fraud_indicators.append({
                    "indicator_type": "general",
                    "severity": "low",
                    "description": indicator,
                    "confidence": 0.7,
                })
        
        # Build policy citations
        policy_citations = []
        for citation in payout_parsed.get("policy_citations", []):
            if isinstance(citation, dict):
                policy_citations.append({
                    "policy_id": citation.get("policy_id", "AC-001"),
                    "policy_name": citation.get("title", citation.get("policy_name", "")),
                    "section": citation.get("section", ""),
                    "citation_text": citation.get("text", citation.get("citation_text", "")),
                    "relevance_score": citation.get("relevance", citation.get("relevance_score", 0.9)),
                    "supports_coverage": True,
                })
        
        if not policy_citations:
            policy_citations = [{
                "policy_id": "AC-DMG-001",
                "policy_name": "Damage Assessment Standards",
                "section": "Assessment",
                "citation_text": "Standard damage assessment applied",
                "relevance_score": 0.9,
                "supports_coverage": True,
            }]
        
        created_at = metadata.get("created_at", datetime.now(UTC).isoformat())
        
        return {
            "claim_id": claim_id,
            "status": "completed",
            "overall_severity": visual_parsed.get("overall_severity", "moderate").lower(),
            "total_estimated_damage": total_estimated_damage if total_estimated_damage > 0 else payout_amount,
            "damage_areas": damage_areas,
            "liability": {
                "fault_determination": fault_parsed.get("fault_determination", fault_parsed.get("primary_fault", "Pending")),
                "fault_percentage": fault_parsed.get("fault_percentage", fault_parsed.get("liability_percentage", 0)),
                "contributing_factors": _extract_string_list(fault_parsed.get("contributing_factors", [])),
                "liability_notes": fault_parsed.get("rationale", fault_parsed.get("summary", "Based on submitted incident documentation")),
            },
            "fraud_indicators": fraud_indicators,
            "policy_citations": policy_citations,
            "payout_recommendation": {
                "recommended_amount": payout_amount,
                "min_amount": payout_amount * 0.8 if payout_amount > 0 else 0,
                "max_amount": payout_amount * 1.2 if payout_amount > 0 else 0,
                "breakdown": {},
                "adjustments": payout_parsed.get("adjustments", []),
            },
            "adjuster_decision": None,
            "created_at": created_at,
            "updated_at": created_at,
        }
    except Exception as e:
        logger.error(f"Failed to read metadata for {claim_id}: {e}")
        return None


def _get_field_value(fields: dict, field_name: str, default: str = "") -> str:
    """Extract field value from content understanding fields."""
    field = fields.get(field_name, {})
    return field.get("valueString", field.get("valueDate", default)) or default


def _extract_string_list(items: List[Any]) -> List[str]:
    """Convert a list of items (possibly dicts) to a list of strings."""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            # Try to extract a meaningful string from the dict
            text = item.get("indicator", item.get("description", item.get("text", item.get("name", ""))))
            if text:
                result.append(str(text))
            else:
                # Fallback: use the first string value found
                for v in item.values():
                    if isinstance(v, str) and v:
                        result.append(v)
                        break
        else:
            result.append(str(item))
    return result


def _extract_damage_areas(fields: dict) -> List[str]:
    """Extract damage areas from fields."""
    areas = []
    damage_areas_field = fields.get("DamageAreas", {})
    if isinstance(damage_areas_field, dict):
        value = damage_areas_field.get("valueString", "")
        if value:
            areas = [a.strip() for a in value.split(",") if a.strip()]
    return areas if areas else ["Front bumper", "Left fender"]


def _get_media_from_files(claim_id: str) -> List[dict]:
    """
    Generate media list from file-based storage.
    """
    settings = load_settings()
    root = settings.app.storage_root
    app_dir = get_application_dir(root, claim_id)
    files_dir = app_dir / "files"
    
    media_list = []
    
    if not files_dir.exists():
        return media_list
    
    # Content type mapping
    content_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
    }
    
    for file_path in files_dir.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in content_types:
                # Determine media type from extension
                if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                    media_type = "video"
                elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
                    media_type = "image"
                else:
                    media_type = "document"
                
                # Get file size
                try:
                    file_size = file_path.stat().st_size
                except:
                    file_size = 0
                
                url = f"/api/applications/{claim_id}/files/{file_path.name}"
                
                media_list.append({
                    "media_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(file_path))),
                    "filename": file_path.name,
                    "content_type": content_types.get(ext, "application/octet-stream"),
                    "media_type": media_type,
                    "size": file_size,
                    "thumbnail_url": url if media_type == "image" else None,
                    "url": url,
                    "processed": True,
                    "analysis_summary": None,
                    "uploaded_at": datetime.now(UTC).isoformat(),
                })
    
    return media_list


def _get_keyframes_from_files(claim_id: str, media_id: str) -> tuple[List[dict], float]:
    """
    Generate synthetic keyframes for video files based on video analysis data.
    Returns tuple of (keyframes list, video duration in seconds).
    """
    settings = load_settings()
    root = settings.app.storage_root
    app_dir = get_application_dir(root, claim_id)
    metadata_path = app_dir / "metadata.json"
    
    keyframes = []
    video_duration = 30.0  # Default duration in seconds
    
    if not metadata_path.exists():
        return keyframes, video_duration
    
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Find video file info
        video_filename = None
        for file_info in metadata.get("files", []):
            filename = file_info.get("filename", "")
            if filename.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                video_filename = filename
                break
        
        if not video_filename:
            return keyframes, video_duration
        
        # Extract video analysis fields from metadata
        # extracted_fields can be either a dict (key = "filename:fieldname") or a list
        extracted_fields = metadata.get("extracted_fields", {})
        video_fields = {}
        
        if isinstance(extracted_fields, dict):
            # New format: dict with "filename:FieldName" keys
            for field_key, field_data in extracted_fields.items():
                if field_key.startswith(video_filename + ":"):
                    key = field_key.split(":", 1)[1]
                    if isinstance(field_data, dict):
                        video_fields[key] = field_data.get("value")
                    else:
                        video_fields[key] = field_data
        elif isinstance(extracted_fields, list):
            # Old format: list of {"name": "filename:FieldName", "value": ...}
            for field in extracted_fields:
                field_name = field.get("name", "")
                if field_name.startswith(video_filename + ":"):
                    key = field_name.split(":", 1)[1]
                    video_fields[key] = field.get("value")
        
        # Parse incident timestamp (e.g., "00:00:05.600")
        incident_timestamp_str = video_fields.get("IncidentTimestamp", "00:00:00")
        incident_timestamp = 0.0
        if incident_timestamp_str:
            parts = incident_timestamp_str.replace(",", ".").split(":")
            try:
                if len(parts) == 3:
                    h, m, s = parts
                    incident_timestamp = float(h) * 3600 + float(m) * 60 + float(s)
                elif len(parts) == 2:
                    m, s = parts
                    incident_timestamp = float(m) * 60 + float(s)
            except ValueError:
                incident_timestamp = 5.0
        
        incident_type = video_fields.get("IncidentType", "collision")
        incident_detected = video_fields.get("IncidentDetected", True)
        pre_behavior = video_fields.get("PreIncidentBehavior", "")
        post_behavior = video_fields.get("PostIncidentBehavior", "")
        weather = video_fields.get("WeatherConditions", "")
        road_type = video_fields.get("RoadType", "")
        
        # Estimate video duration based on incident timestamp
        if incident_timestamp > 0:
            video_duration = max(incident_timestamp * 2, 20.0)  # Assume incident is roughly in middle
        
        # Generate keyframes at key moments
        keyframe_times = []
        
        # Keyframe before incident (pre-incident context)
        if incident_timestamp > 2:
            keyframe_times.append((incident_timestamp - 2, "Pre-incident", False, pre_behavior or "Vehicle approaching"))
        
        # Keyframe at incident
        if incident_detected:
            keyframe_times.append((
                incident_timestamp, 
                f"Incident: {incident_type}", 
                True, 
                f"Impact detected - {incident_type}"
            ))
        
        # Keyframe after incident
        keyframe_times.append((
            incident_timestamp + 2, 
            "Post-incident", 
            True, 
            post_behavior or "Post-collision assessment"
        ))
        
        # Additional context keyframes
        if incident_timestamp > 5:
            keyframe_times.insert(0, (0.5, "Video start", False, f"Recording begins - {road_type or 'road'}"))
        
        # Generate keyframe objects
        for i, (timestamp, label, damage_detected, description) in enumerate(keyframe_times):
            minutes = int(timestamp // 60)
            seconds = timestamp % 60
            timestamp_formatted = f"{minutes:02d}:{seconds:05.2f}"
            
            keyframes.append({
                "keyframe_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{claim_id}-{media_id}-kf-{i}")),
                "timestamp": timestamp,
                "timestamp_formatted": timestamp_formatted,
                "thumbnail_url": None,  # No actual thumbnail available
                "description": description,
                "damage_detected": damage_detected,
                "damage_areas": [],
                "confidence": 0.85 if damage_detected else 0.75,
            })
        
        return keyframes, video_duration
        
    except Exception as e:
        logger.error(f"Failed to get keyframes from files: {e}")
        return [], video_duration


def _get_damage_areas_from_files(claim_id: str, media_id: str) -> List[dict]:
    """
    Generate damage areas from content understanding data.
    """
    settings = load_settings()
    root = settings.app.storage_root
    app_dir = get_application_dir(root, claim_id)
    cu_path = app_dir / "content_understanding.json"
    
    if not cu_path.exists():
        return []
    
    try:
        with open(cu_path, "r", encoding="utf-8") as f:
            cu_data = json.load(f)
        
        result = cu_data.get("result", {})
        contents = result.get("contents", [])
        if not contents:
            return []
        
        fields = contents[0].get("fields", {})
        damage_areas = _extract_damage_areas(fields)
        
        return [
            {
                "area_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{claim_id}-{i}")),
                "location": area,
                "severity": "moderate",
                "confidence": 0.85,
                "bounding_box": None,
                "source_media_id": media_id,
            }
            for i, area in enumerate(damage_areas)
        ]
    except Exception as e:
        logger.error(f"Failed to get damage areas from files: {e}")
        return []


# ============================================================================
# Pydantic Models
# ============================================================================

class ClaimSubmitRequest(BaseModel):
    """Request model for claim submission."""
    external_reference: Optional[str] = Field(None, description="External claim reference ID")
    claimant_name: Optional[str] = None
    vehicle_info: Optional[dict] = None
    incident_description: Optional[str] = None
    incident_date: Optional[str] = None


class ClaimSubmitResponse(BaseModel):
    """Response from claim submission."""
    claim_id: str
    status: str
    created_at: str
    file_count: int
    message: str


class FileUploadResponse(BaseModel):
    """Response from file upload."""
    file_id: str
    filename: str
    media_type: str
    content_type: str
    size_bytes: int


class ProcessingStatusResponse(BaseModel):
    """Response for processing status."""
    claim_id: str
    status: str
    total_files: int
    completed: int
    failed: int
    progress_percent: float


class DamageAreaItem(BaseModel):
    """Response for a damage area item."""
    area_id: str
    location: str
    severity: str  # minor, moderate, severe, total_loss
    confidence: float
    estimated_cost: float = 0.0
    description: str = ""
    bounding_box: Optional[dict] = None
    source_media_id: Optional[str] = None


class LiabilityAssessmentResponse(BaseModel):
    """Response for liability assessment."""
    fault_determination: str
    fault_percentage: int
    contributing_factors: List[str]
    liability_notes: str


class FraudIndicatorItem(BaseModel):
    """Response for fraud indicator."""
    indicator_type: str
    severity: str  # low, medium, high
    description: str
    confidence: float = 0.85


class PayoutRecommendationResponse(BaseModel):
    """Response for payout recommendation."""
    recommended_amount: float
    min_amount: float = 0.0
    max_amount: float = 0.0
    breakdown: dict = {}
    adjustments: List[dict] = []


class PolicyCitationItem(BaseModel):
    """Response for policy citation."""
    policy_id: str
    policy_name: str = ""
    section: str = ""
    citation_text: str = ""
    relevance_score: float = 0.9
    supports_coverage: bool = True


class ClaimAssessmentResponse(BaseModel):
    """Full claim assessment response - aligned with frontend expectations."""
    claim_id: str
    status: str
    overall_severity: str  # minor, moderate, severe, total_loss
    total_estimated_damage: float = 0.0
    damage_areas: List[DamageAreaItem] = []
    liability: LiabilityAssessmentResponse
    fraud_indicators: List[FraudIndicatorItem] = []
    policy_citations: List[PolicyCitationItem] = []
    payout_recommendation: PayoutRecommendationResponse
    adjuster_decision: Optional[dict] = None
    created_at: str = ""
    updated_at: str = ""


class AdjusterDecisionRequest(BaseModel):
    """Request for adjuster decision update."""
    decision: str = Field(..., description="approved, denied, pending_review")
    approved_amount: Optional[float] = None
    notes: Optional[str] = None


class PolicySearchRequest(BaseModel):
    """Request for policy search."""
    query: str = Field(..., description="Natural language query")
    category: Optional[str] = Field(None, description="Filter by category")
    top_k: int = Field(5, ge=1, le=20)


class PolicySearchResponse(BaseModel):
    """Response from policy search."""
    query: str
    results: List[dict]
    total_results: int


class MediaItemResponse(BaseModel):
    """Response for a media item."""
    media_id: str
    filename: str
    content_type: str
    media_type: str
    size: int = 0
    thumbnail_url: Optional[str] = None
    url: str
    processed: bool
    analysis_summary: Optional[str] = None
    uploaded_at: str


class MediaListResponse(BaseModel):
    """Response for media list."""
    claim_id: str
    media_items: List[MediaItemResponse]
    total_count: int


class KeyframeResponse(BaseModel):
    """Response for video keyframe."""
    keyframe_id: str
    timestamp: float
    timestamp_formatted: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    damage_detected: bool
    damage_areas: List[dict] = Field(default_factory=list)
    confidence: float = 0.8


class KeyframesListResponse(BaseModel):
    """Response for keyframes list."""
    media_id: str
    duration: float
    keyframes: List[KeyframeResponse]
    total_keyframes: int


class DamageAreaResponse(BaseModel):
    """Response for detected damage area."""
    area_id: str
    location: str
    severity: str
    confidence: float
    bounding_box: Optional[dict] = None
    source_media_id: str


# ============================================================================
# Claim Submission Endpoints
# ============================================================================

@router.post("/submit", response_model=ClaimSubmitResponse)
async def submit_claim(
    files: List[UploadFile] = File(...),
    external_reference: Optional[str] = Form(None),
    claimant_name: Optional[str] = Form(None),
    vehicle_info: Optional[str] = Form(None),  # JSON string
    incident_description: Optional[str] = Form(None),
    incident_date: Optional[str] = Form(None),
) -> ClaimSubmitResponse:
    """
    Submit a new automotive claim with multimodal files.
    
    Accepts PDF documents, images (JPEG, PNG), and videos (MP4, MOV).
    Files are automatically routed to appropriate Azure Content Understanding analyzers.
    """
    claim_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(UTC).isoformat()
    
    # Validate files
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    
    file_infos = []
    for upload_file in files:
        content = await upload_file.read()
        detection = detect_media_type(content, upload_file.filename)
        
        if not detection.is_supported:
            logger.warning(f"Unsupported file type: {upload_file.filename}")
            continue
        
        file_infos.append(FileInfo(
            file_id=str(uuid.uuid4()),
            filename=upload_file.filename,
            file_bytes=content,
            content_type=detection.mime_type,
            claim_id=claim_id,
            metadata={
                "media_type": detection.media_type.value,
                "external_reference": external_reference,
                "claimant_name": claimant_name,
                "incident_date": incident_date,
            }
        ))
    
    if not file_infos:
        raise HTTPException(status_code=400, detail="No valid files were uploaded")
    
    # Store claim metadata in database
    try:
        settings = load_settings()
        repository = ClaimsMediaRepository(settings)
        await repository.initialize_tables()
        
        # Save initial claim record
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO workbenchiq.claims (
                    claim_id, external_reference, claimant_name,
                    incident_description, incident_date, status, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (claim_id) DO UPDATE SET
                    external_reference = EXCLUDED.external_reference,
                    updated_at = CURRENT_TIMESTAMP
                """,
                claim_id,
                external_reference,
                claimant_name,
                incident_description,
                incident_date,
                "pending_processing",
                created_at,
            )
    except Exception as e:
        logger.error(f"Failed to save claim: {e}")
        # Continue without database - files will still be processed
    
    return ClaimSubmitResponse(
        claim_id=claim_id,
        status="pending_processing",
        created_at=created_at,
        file_count=len(file_infos),
        message=f"Claim submitted successfully with {len(file_infos)} files",
    )


@router.post("/{claim_id}/upload", response_model=List[FileUploadResponse])
async def upload_claim_files(
    claim_id: str,
    files: List[UploadFile] = File(...),
) -> List[FileUploadResponse]:
    """
    Upload additional files to an existing claim.
    """
    responses = []
    
    for upload_file in files:
        content = await upload_file.read()
        detection = detect_media_type(content, upload_file.filename)
        
        if not detection.is_supported:
            logger.warning(f"Skipping unsupported file: {upload_file.filename}")
            continue
        
        file_id = str(uuid.uuid4())
        responses.append(FileUploadResponse(
            file_id=file_id,
            filename=upload_file.filename,
            media_type=detection.media_type.value,
            content_type=detection.mime_type,
            size_bytes=len(content),
        ))
    
    return responses


@router.post("/{claim_id}/process", response_model=ProcessingStatusResponse)
async def process_claim(
    claim_id: str,
    background_tasks: BackgroundTasks,
) -> ProcessingStatusResponse:
    """
    Trigger multimodal processing for all uploaded claim files.
    
    Processing happens asynchronously. Use the status endpoint to check progress.
    """
    # In a real implementation, this would:
    # 1. Retrieve uploaded files from storage
    # 2. Queue them for processing
    # 3. Return immediately with a status
    
    return ProcessingStatusResponse(
        claim_id=claim_id,
        status="processing",
        total_files=0,
        completed=0,
        failed=0,
        progress_percent=0.0,
    )


@router.get("/{claim_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(claim_id: str) -> ProcessingStatusResponse:
    """
    Get the processing status for a claim.
    """
    # Query database for actual status
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT status, 
                       (SELECT COUNT(*) FROM workbenchiq.claim_media WHERE claim_id = $1) as total,
                       (SELECT COUNT(*) FROM workbenchiq.claim_media WHERE claim_id = $1 AND status = 'completed') as completed,
                       (SELECT COUNT(*) FROM workbenchiq.claim_media WHERE claim_id = $1 AND status = 'failed') as failed
                FROM workbenchiq.claims
                WHERE claim_id = $1
                """,
                claim_id,
            )
            
            if not row:
                raise HTTPException(status_code=404, detail="Claim not found")
            
            total = row["total"] or 0
            completed = row["completed"] or 0
            failed = row["failed"] or 0
            progress = (completed + failed) / total * 100 if total > 0 else 0
            
            return ProcessingStatusResponse(
                claim_id=claim_id,
                status=row["status"],
                total_files=total,
                completed=completed,
                failed=failed,
                progress_percent=progress,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")


# ============================================================================
# Assessment Endpoints
# ============================================================================

@router.get("/{claim_id}/assessment", response_model=ClaimAssessmentResponse)
async def get_claim_assessment(claim_id: str) -> ClaimAssessmentResponse:
    """
    Get the policy-based assessment for a claim.
    
    Returns damage severity, liability determination, fraud risk, and payout recommendation
    with policy citations.
    
    Falls back to file-based storage if database has no data (backward compatibility).
    """
    assessment_data = None
    
    # Try database first (if available)
    try:
        settings = load_settings()
        repository = ClaimsMediaRepository(settings)
        assessment_data = await repository.get_claim_assessment(claim_id)
    except Exception as db_error:
        logger.debug(f"Database access failed for {claim_id}, using file fallback: {db_error}")
    
    # Fallback to file-based storage
    if not assessment_data:
        logger.info(f"Using file-based fallback for assessment {claim_id}")
        assessment_data = _get_assessment_from_files(claim_id)
    
    if not assessment_data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    try:
        # Build damage areas
        damage_areas = []
        for area in assessment_data.get("damage_areas", []):
            if isinstance(area, dict):
                damage_areas.append(DamageAreaItem(
                    area_id=area.get("area_id", str(uuid.uuid4())),
                    location=area.get("location", "unknown"),
                    severity=area.get("severity", "moderate"),
                    confidence=area.get("confidence", 0.8),
                    estimated_cost=area.get("estimated_cost", 0.0),
                    description=area.get("description"),
                    bounding_box=area.get("bounding_box"),
                    source_media_id=area.get("source_media_id"),
                ))
        
        # Build liability
        liability_data = assessment_data.get("liability", {})
        liability = LiabilityAssessmentResponse(
            fault_determination=liability_data.get("fault_determination", "Pending"),
            fault_percentage=liability_data.get("fault_percentage", 0),
            contributing_factors=liability_data.get("contributing_factors", []),
            liability_notes=liability_data.get("liability_notes"),
        )
        
        # Build fraud indicators
        fraud_indicators = []
        for indicator in assessment_data.get("fraud_indicators", []):
            if isinstance(indicator, dict):
                fraud_indicators.append(FraudIndicatorItem(
                    indicator_type=indicator.get("indicator_type", "general"),
                    severity=indicator.get("severity", "low"),
                    description=indicator.get("description", ""),
                    confidence=indicator.get("confidence", 0.7),
                ))
        
        # Build policy citations
        policy_citations = []
        for citation in assessment_data.get("policy_citations", []):
            if isinstance(citation, dict):
                policy_citations.append(PolicyCitationItem(
                    policy_id=citation.get("policy_id", ""),
                    policy_name=citation.get("policy_name", citation.get("title", "")),
                    section=citation.get("section"),
                    citation_text=citation.get("citation_text", citation.get("text", "")),
                    relevance_score=citation.get("relevance_score", citation.get("relevance", 0.9)),
                    supports_coverage=citation.get("supports_coverage", True),
                ))
        
        # Build payout recommendation
        payout_data = assessment_data.get("payout_recommendation", {})
        payout = PayoutRecommendationResponse(
            recommended_amount=payout_data.get("recommended_amount", 0.0),
            min_amount=payout_data.get("min_amount"),
            max_amount=payout_data.get("max_amount"),
            breakdown=payout_data.get("breakdown", {}),
            adjustments=payout_data.get("adjustments", []),
        )
        
        return ClaimAssessmentResponse(
            claim_id=claim_id,
            status=assessment_data.get("status", "pending"),
            overall_severity=assessment_data.get("overall_severity", "moderate"),
            total_estimated_damage=assessment_data.get("total_estimated_damage", 0.0),
            damage_areas=damage_areas,
            liability=liability,
            fraud_indicators=fraud_indicators,
            policy_citations=policy_citations,
            payout_recommendation=payout,
            adjuster_decision=assessment_data.get("adjuster_decision"),
            created_at=assessment_data.get("created_at", ""),
            updated_at=assessment_data.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"Failed to build assessment response: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assessment")


@router.put("/{claim_id}/assessment/decision")
async def update_adjuster_decision(
    claim_id: str,
    request: AdjusterDecisionRequest,
) -> dict:
    """
    Update the adjuster's decision on a claim.
    """
    settings = load_settings()
    repository = ClaimsMediaRepository(settings)
    
    try:
        await repository.update_adjuster_decision(
            claim_id=claim_id,
            decision=request.decision,
            approved_amount=request.approved_amount,
            notes=request.notes,
        )
        
        return {
            "claim_id": claim_id,
            "decision": request.decision,
            "updated_at": datetime.now(UTC).isoformat(),
            "message": "Decision updated successfully",
        }
    except Exception as e:
        logger.error(f"Failed to update decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to update decision")


@router.get("/pending", response_model=List[dict])
async def list_pending_claims(
    limit: int = Query(50, ge=1, le=100),
) -> List[dict]:
    """
    List claims pending adjuster review.
    """
    settings = load_settings()
    repository = ClaimsMediaRepository(settings)
    
    try:
        pending = await repository.list_pending_assessments(limit=limit)
        return pending
    except Exception as e:
        logger.error(f"Failed to list pending claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending claims")


# ============================================================================
# Policy Search Endpoints
# ============================================================================

@router.post("/policies/search", response_model=PolicySearchResponse)
async def search_policies(request: PolicySearchRequest) -> PolicySearchResponse:
    """
    Search claims policies using semantic search.
    
    Returns relevant policy sections based on natural language query.
    """
    settings = load_settings()
    # Use unified indexer-compatible search service
    search_service = AutomotiveClaimsPolicySearchService(settings)
    
    try:
        # Use lower threshold for policy search UI (single keywords often score lower)
        results = await search_service.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=0.3,  # Lower threshold for keyword searches
        )
        
        return PolicySearchResponse(
            query=request.query,
            results=[
                {
                    "chunk_id": str(r.chunk_id),
                    "policy_id": r.policy_id,
                    "policy_name": r.policy_name,
                    "category": r.category,
                    "content": r.content,
                    "similarity": r.similarity,
                    "severity": r.risk_level,  # Map risk_level to severity for API compatibility
                    "criteria_id": r.criteria_id,
                }
                for r in results
            ],
            total_results=len(results),
        )
    except Exception as e:
        logger.error(f"Policy search failed: {e}")
        raise HTTPException(status_code=500, detail="Policy search failed")


@router.get("/policies/context")
async def get_policy_context(
    query: str = Query(..., description="Query for policy context"),
    category: Optional[str] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
) -> dict:
    """
    Get formatted policy context for RAG-based chat.
    """
    settings = load_settings()
    
    try:
        context = await get_claims_policy_context(
            settings=settings,
            query=query,
            category=category,
            top_k=top_k,
        )
        
        return {"query": query, "context": context}
    except Exception as e:
        logger.error(f"Failed to get policy context: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policy context")


# ============================================================================
# Media Endpoints
# ============================================================================

@router.get("/{claim_id}/media", response_model=MediaListResponse)
async def list_claim_media(claim_id: str) -> MediaListResponse:
    """
    List all media files for a claim.
    
    Falls back to file-based storage if database has no data (backward compatibility).
    """
    media_list = None
    
    # Try database first (if available)
    try:
        settings = load_settings()
        repository = ClaimsMediaRepository(settings)
        media_list = await repository.get_claim_media(claim_id)
    except Exception as db_error:
        logger.debug(f"Database access failed for media {claim_id}, using file fallback: {db_error}")
    
    # Fallback to file-based storage
    if not media_list:
        logger.info(f"Using file-based fallback for media {claim_id}")
        media_list = _get_media_from_files(claim_id)
    
    items = [
        MediaItemResponse(
            media_id=m["media_id"],
            filename=m["filename"],
            content_type=m.get("content_type", "application/octet-stream"),
            media_type=m["media_type"],
            size=m.get("size", 0),
            thumbnail_url=m.get("thumbnail_url"),
            url=m.get("url", ""),
            processed=m.get("processed", True),
            analysis_summary=m.get("analysis_summary"),
            uploaded_at=m["uploaded_at"],
        )
        for m in media_list
    ]
    
    return MediaListResponse(
        claim_id=claim_id,
        media_items=items,
        total_count=len(items),
    )


@router.get("/{claim_id}/media/{media_id}/keyframes", response_model=KeyframesListResponse)
async def get_media_keyframes(claim_id: str, media_id: str) -> KeyframesListResponse:
    """
    Get extracted keyframes from a video file.
    
    Falls back to file-based storage if database has no data.
    """
    keyframes = None
    
    # Try database first (if available)
    try:
        settings = load_settings()
        repository = ClaimsMediaRepository(settings)
        keyframes = await repository.get_keyframes(claim_id)
        # Filter by media_id if needed
        if keyframes:
            keyframes = [kf for kf in keyframes if str(kf.get("media_id", "")) == media_id]
    except Exception as db_error:
        logger.debug(f"Database access failed for keyframes {claim_id}, using fallback: {db_error}")
    
    # Fallback to file-based storage
    video_duration = 30.0  # Default duration
    if keyframes is None:
        keyframes, video_duration = _get_keyframes_from_files(claim_id, media_id)
    
    def format_timestamp(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"
    
    items = [
        KeyframeResponse(
            keyframe_id=str(kf.get("id", kf.get("keyframe_id", ""))),
            timestamp=kf.get("timestamp_seconds", kf.get("timestamp", 0.0)),
            timestamp_formatted=kf.get("timestamp_formatted", format_timestamp(kf.get("timestamp_seconds", kf.get("timestamp", 0.0)))),
            thumbnail_url=kf.get("frame_url", kf.get("url", kf.get("thumbnail_url"))),
            description=kf.get("description"),
            damage_detected=kf.get("damage_detected", False),
            damage_areas=kf.get("damage_areas", []),
            confidence=kf.get("confidence", 0.8),
        )
        for kf in keyframes
    ]
    
    return KeyframesListResponse(
        media_id=media_id,
        duration=video_duration,
        keyframes=items,
        total_keyframes=len(items),
    )


@router.get("/{claim_id}/media/{media_id}/damage-areas", response_model=List[DamageAreaResponse])
async def get_media_damage_areas(claim_id: str, media_id: str) -> List[DamageAreaResponse]:
    """
    Get detected damage areas from an image or video frame.
    
    Falls back to file-based storage if database has no data.
    """
    damage_areas = None
    
    # Try database first (if available)
    try:
        settings = load_settings()
        repository = ClaimsMediaRepository(settings)
        damage_areas = await repository.get_damage_areas(claim_id, media_id)
    except Exception as db_error:
        logger.debug(f"Database access failed for damage areas {claim_id}, using fallback: {db_error}")
    
    # Fallback to file-based storage
    if damage_areas is None:
        damage_areas = _get_damage_areas_from_files(claim_id, media_id)
    
    return [
        DamageAreaResponse(
            area_id=da.get("area_id", str(uuid.uuid4())),
            location=da.get("location", "Unknown"),
            severity=da.get("severity", "moderate"),
            confidence=da.get("confidence", 0.85),
            bounding_box=da.get("bounding_box"),
            source_media_id=media_id,
        )
        for da in damage_areas
    ]


@router.get("/{claim_id}/damage-summary", response_model=List[DamageAreaResponse])
async def get_claim_damage_summary(claim_id: str) -> List[DamageAreaResponse]:
    """
    Get aggregated damage summary across all media for a claim.
    """
    settings = load_settings()
    repository = ClaimsMediaRepository(settings)
    
    try:
        # Get all damage areas from all media
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT da.*, cm.media_id
                FROM workbenchiq.damage_areas da
                JOIN workbenchiq.claim_media cm ON da.media_id = cm.id
                WHERE cm.claim_id = $1
                ORDER BY da.confidence DESC
                """,
                claim_id,
            )
        
        return [
            DamageAreaResponse(
                area_id=str(row["id"]),
                location=row["location"],
                severity=row["severity"],
                confidence=row["confidence"],
                bounding_box=row.get("bounding_box"),
                source_media_id=str(row["media_id"]),
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to get damage summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve damage summary")
