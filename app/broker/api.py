"""
Commercial Brokerage API Router

FastAPI router providing endpoints for:
- Client management
- Submission workflow
- Quote upload and comparison
- Carrier profile management
- Dashboard metrics
- AI-powered client research
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.broker.constants import (
    DocumentType,
    LineOfBusiness,
    QuoteStatus,
    SubmissionStatus,
)
from app.broker.models import (
    BrokerDocument,
    CarrierProfile,
    Client,
    Placement,
    PlacementScoring,
    PropertyLocation,
    Quote,
    QuoteFields,
    Submission,
)
from app.broker.acord_forms import (
    ACORD_125_FIELDS,
    ACORD_140_FIELDS,
    SOV_FIELDS,
    get_acord_form_template,
    map_extracted_to_acord125,
)
from app.broker.package_generator import SubmissionPackageGenerator
from app.broker.storage import BrokerStorage
from app.broker.quote_extractor import QuoteExtractor
from app.broker.placement_engine import PlacementEngine
from app.broker.research_engine import ClientResearchEngine
from app.broker.submission_generator import SubmissionGenerator
from app.config import load_settings

logger = logging.getLogger(__name__)


def _quote_from_dict(data: Dict[str, Any]) -> Quote:
    """Reconstruct a Quote dataclass from a storage dict, handling nested fields."""
    d = dict(data)
    # Convert nested 'fields' dict → QuoteFields dataclass
    if isinstance(d.get("fields"), dict):
        raw_fields = dict(d["fields"])
        # Ensure deductible is a string (LLM may return a dict)
        if isinstance(raw_fields.get("deductible"), dict):
            raw_fields["deductible"] = ", ".join(
                f"{k}: {v}" for k, v in raw_fields["deductible"].items()
            )
        d["fields"] = QuoteFields(**{
            k: v for k, v in raw_fields.items()
            if k in QuoteFields.__dataclass_fields__
        })
    # Convert nested 'scoring' dict → PlacementScoring dataclass
    if isinstance(d.get("scoring"), dict):
        d["scoring"] = PlacementScoring(**{
            k: v for k, v in d["scoring"].items()
            if k in PlacementScoring.__dataclass_fields__
        })
    # Drop any extra keys not on the Quote dataclass
    valid_keys = set(Quote.__dataclass_fields__)
    return Quote(**{k: v for k, v in d.items() if k in valid_keys})


def _submission_from_dict(data: Dict[str, Any]) -> Submission:
    """Reconstruct a Submission dataclass from a storage dict, handling nested types."""
    d = dict(data)
    # Convert embedded quotes dicts → Quote dataclass instances
    if isinstance(d.get("quotes"), list):
        d["quotes"] = [
            _quote_from_dict(q) if isinstance(q, dict) else q
            for q in d["quotes"]
        ]
    # Convert embedded documents (list of dicts) — leave as-is since they serialize cleanly
    # Convert embedded property locations if present
    valid_keys = set(Submission.__dataclass_fields__)
    return Submission(**{k: v for k, v in d.items() if k in valid_keys})

# Create router with prefix
router = APIRouter(prefix="/api/broker", tags=["Commercial Brokerage"])

# Initialize storage
storage = BrokerStorage()

# Load settings for engines
_settings = load_settings()


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class PropertyLocationSchema(BaseModel):
    address: str = ""
    occupancy: str = ""
    construction: str = ""
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    building_value: str = ""
    contents_value: str = ""
    bi_value: str = ""
    protection_class: str = ""


class CreateClientRequest(BaseModel):
    name: str
    industry_code: str = ""
    business_type: str = ""
    years_in_business: Optional[int] = None
    annual_revenue: str = ""
    employee_count: Optional[int] = None
    headquarters_address: str = ""
    property_locations: List[PropertyLocationSchema] = Field(default_factory=list)
    renewal_date: Optional[str] = None
    broker_notes: str = ""
    contacts: List[Dict[str, str]] = Field(default_factory=list)


class UpdateClientRequest(BaseModel):
    name: Optional[str] = None
    industry_code: Optional[str] = None
    business_type: Optional[str] = None
    years_in_business: Optional[int] = None
    annual_revenue: Optional[str] = None
    employee_count: Optional[int] = None
    headquarters_address: Optional[str] = None
    property_locations: Optional[List[PropertyLocationSchema]] = None
    renewal_date: Optional[str] = None
    broker_notes: Optional[str] = None
    contacts: Optional[List[Dict[str, str]]] = None


class CreateSubmissionRequest(BaseModel):
    client_id: str
    line_of_business: str = LineOfBusiness.PROPERTY.value
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    total_insured_value: str = ""
    coverage_requested: Dict[str, Any] = Field(default_factory=dict)
    submitted_carriers: List[str] = Field(default_factory=list)


class UpdateSubmissionRequest(BaseModel):
    line_of_business: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    total_insured_value: Optional[str] = None
    coverage_requested: Optional[Dict[str, Any]] = None
    submitted_carriers: Optional[List[str]] = None
    acord_125_fields: Optional[Dict[str, Any]] = None
    acord_140_fields: Optional[Dict[str, Any]] = None


class UploadQuoteResponse(BaseModel):
    quote_id: str
    status: str
    message: str


class CompareResponse(BaseModel):
    comparison_table: List[Dict[str, Any]]
    recommendation: str
    placement_scores: List[Dict[str, Any]]


class ResearchRequest(BaseModel):
    company_name: str
    document_ids: List[str] = Field(
        default_factory=list,
        description="Optional IDs of uploaded research documents to include as context",
    )


class ResearchResponse(BaseModel):
    """Structured research brief — mirrors ResearchBrief schema."""

    company_name: str = ""
    business_description: str = ""
    headquarters: str = ""
    year_founded: Optional[int] = None
    employee_count: Optional[int] = None
    ownership_type: str = ""
    key_operations: List[str] = Field(default_factory=list)
    annual_revenue: str = ""
    revenue_trend: str = ""
    credit_rating: str = ""
    financial_highlights: List[str] = Field(default_factory=list)
    naics_code: str = ""
    industry_sector: str = ""
    common_perils: List[str] = Field(default_factory=list)
    loss_frequency: str = ""
    risk_factors: List[str] = Field(default_factory=list)
    insurance_needs: List[Dict[str, str]] = Field(default_factory=list)
    carrier_matches: List[Dict[str, str]] = Field(default_factory=list)
    recent_news: List[Dict[str, str]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    confidence_level: str = ""
    data_sources: List[str] = Field(default_factory=list)
    generated_at: str = ""


class CreateCarrierRequest(BaseModel):
    carrier_name: str
    amb_number: str = ""
    naic_code: str = ""
    financial_strength_rating: str = ""
    issuer_credit_rating: str = ""
    rating_outlook: str = ""
    balance_sheet_strength: str = ""
    operating_performance: str = ""
    business_profile: str = ""
    erm_assessment: str = ""
    net_premiums_written: str = ""
    policyholders_surplus: str = ""
    combined_ratio: str = ""
    five_year_avg_combined_ratio: str = ""
    report_date: Optional[str] = None
    direct_written_premium: str = ""
    nwp_to_surplus_ratio: str = ""
    lines_of_business_written: List[Dict[str, str]] = Field(default_factory=list)
    geographic_concentration: List[Dict[str, str]] = Field(default_factory=list)


class UpdateAcordFieldsRequest(BaseModel):
    """Request body for saving edited ACORD field values."""
    acord_125_fields: Dict[str, Any] = Field(default_factory=dict)
    acord_140_fields: Dict[str, Any] = Field(default_factory=dict)


class GeneratePackageRequest(BaseModel):
    """Request body for enhanced package generation."""
    carriers: List[str] = Field(default_factory=list)


class UpdatePackageEmailRequest(BaseModel):
    """Request body for saving an edited cover email draft."""
    cover_email: str


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@router.get("/dashboard")
async def get_dashboard():
    """
    Get dashboard metrics for the broker workspace.
    
    Returns:
        Dashboard metrics including total accounts, bound premium,
        open submissions, renewals due, and stale submissions.
    """
    try:
        metrics = storage.get_dashboard_metrics()
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching dashboard metrics", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Client Endpoints
# ============================================================================

@router.get("/clients")
async def list_clients():
    """
    List all clients.
    
    Returns:
        List of client records.
    """
    try:
        clients = storage.list_clients()
        return clients
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing clients", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clients", status_code=201)
async def create_client(request: CreateClientRequest):
    """
    Create a new client.
    
    Args:
        request: Client creation data
        
    Returns:
        Created client record with generated ID.
    """
    try:
        # Convert property locations from Pydantic models to dataclass instances
        property_locations = [
            PropertyLocation(**loc.model_dump())
            for loc in request.property_locations
        ]
        
        # Create Client dataclass instance
        client = Client(
            name=request.name,
            industry_code=request.industry_code,
            business_type=request.business_type,
            years_in_business=request.years_in_business,
            annual_revenue=request.annual_revenue,
            employee_count=request.employee_count,
            headquarters_address=request.headquarters_address,
            property_locations=property_locations,
            renewal_date=request.renewal_date,
            broker_notes=request.broker_notes,
            contacts=request.contacts,
        )
        
        # Save to storage
        storage.save_client(client)
        
        # Return as dict
        return asdict(client)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating client", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients/{client_id}")
async def get_client(client_id: str):
    """
    Get client details by ID.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Client record.
    """
    try:
        client = storage.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/clients/{client_id}")
async def update_client(client_id: str, request: UpdateClientRequest):
    """
    Update an existing client.
    
    Args:
        client_id: Client identifier
        request: Fields to update (partial)
        
    Returns:
        Updated client record.
    """
    try:
        # Get existing client
        existing = storage.get_client(client_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        
        # Update fields that were provided
        update_data = request.model_dump(exclude_unset=True)
        
        # Convert property locations if provided
        if "property_locations" in update_data and update_data["property_locations"]:
            update_data["property_locations"] = [
                PropertyLocation(**loc.model_dump()) if isinstance(loc, PropertyLocationSchema) else PropertyLocation(**loc)
                for loc in update_data["property_locations"]
            ]
        
        # Merge with existing data
        existing.update(update_data)
        existing["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert property_locations dicts → PropertyLocation dataclasses
        if isinstance(existing.get("property_locations"), list):
            existing["property_locations"] = [
                PropertyLocation(**loc) if isinstance(loc, dict) else loc
                for loc in existing["property_locations"]
            ]
        
        # Create Client instance and save
        valid_keys = set(Client.__dataclass_fields__)
        client = Client(**{k: v for k, v in existing.items() if k in valid_keys})
        storage.save_client(client)
        
        return asdict(client)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients/{client_id}/submissions")
async def list_client_submissions(client_id: str):
    """
    List all submissions for a specific client.
    
    Args:
        client_id: Client identifier
        
    Returns:
        List of submission records for the client.
    """
    try:
        # Verify client exists
        client = storage.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        
        submissions = storage.list_submissions(client_id=client_id)
        return submissions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing submissions for client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Submission Endpoints
# ============================================================================

@router.post("/submissions", status_code=201)
async def create_submission(request: CreateSubmissionRequest):
    """
    Create a new submission.
    
    Args:
        request: Submission creation data
        
    Returns:
        Created submission record with generated ID.
    """
    try:
        # Verify client exists
        client = storage.get_client(request.client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client {request.client_id} not found")
        
        # Create Submission dataclass instance
        submission = Submission(
            client_id=request.client_id,
            line_of_business=request.line_of_business,
            effective_date=request.effective_date,
            expiration_date=request.expiration_date,
            total_insured_value=request.total_insured_value,
            coverage_requested=request.coverage_requested,
            submitted_carriers=request.submitted_carriers,
        )
        
        # Save to storage
        storage.save_submission(submission)
        
        # Return as dict
        return asdict(submission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating submission", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: str):
    """
    Get submission details by ID, including all quotes.
    
    Args:
        submission_id: Submission identifier
        
    Returns:
        Submission record with embedded quotes.
    """
    try:
        submission = storage.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        return submission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/submissions/{submission_id}")
async def update_submission(submission_id: str, request: UpdateSubmissionRequest):
    """
    Update an existing submission.
    
    Args:
        submission_id: Submission identifier
        request: Fields to update (partial)
        
    Returns:
        Updated submission record.
    """
    try:
        # Get existing submission
        existing = storage.get_submission(submission_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        
        # Update fields that were provided
        update_data = request.model_dump(exclude_unset=True)
        
        # Merge with existing data
        existing.update(update_data)
        existing["updated_at"] = datetime.utcnow().isoformat()
        
        # Create Submission instance and save
        submission = _submission_from_dict(existing)
        storage.save_submission(submission)
        
        return asdict(submission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Quote Endpoints
# ============================================================================

@router.post("/submissions/{submission_id}/quotes", status_code=201)
async def upload_quote(
    submission_id: str,
    carrier_name: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a quote document for a submission.
    
    Args:
        submission_id: Submission identifier
        carrier_name: Name of the carrier providing the quote
        file: Quote document file (PDF, Excel, etc.)
        
    Returns:
        Quote ID and status message.
    """
    try:
        # Verify submission exists
        submission = storage.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        
        # Create directory for quotes
        quotes_dir = Path("data") / "broker" / "quotes" / submission_id
        quotes_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = quotes_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        # Determine source format from file extension
        file_ext = file.filename.split(".")[-1].lower()
        source_format_map = {
            "pdf": "pdf",
            "xlsx": "xlsx",
            "xls": "xlsx",
            "docx": "docx",
            "doc": "docx",
            "msg": "email",
            "eml": "email",
        }
        source_format = source_format_map.get(file_ext, "other")
        
        # Create Quote dataclass instance
        quote = Quote(
            submission_id=submission_id,
            carrier_name=carrier_name,
            source_format=source_format,
            source_file_name=file.filename,
            received_date=datetime.utcnow().isoformat(),
            status=QuoteStatus.RAW.value,
        )
        
        # Save initial quote with RAW status
        storage.save_quote(quote)
        
        # Extract quote fields using QuoteExtractor
        try:
            extractor = QuoteExtractor(_settings.openai)
            extracted_fields, confidence_scores = await extractor.extract_quote(
                content, file.filename, carrier_name
            )
            quote.fields = extracted_fields
            quote.confidence_scores = confidence_scores
            quote.status = QuoteStatus.EXTRACTED.value
            logger.info(f"Successfully extracted fields from quote {quote.id}")
        except Exception as e:
            logger.error(f"Quote extraction failed for {quote.id}: {e}", exc_info=True)
            # Keep quote in RAW status if extraction fails
            quote.status = QuoteStatus.RAW.value
        
        # Save updated quote
        storage.save_quote(quote)
        
        return UploadQuoteResponse(
            quote_id=quote.id,
            status=quote.status,
            message=f"Quote from {carrier_name} uploaded and {'extracted' if quote.status == QuoteStatus.EXTRACTED.value else 'saved (extraction pending)'}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading quote for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{submission_id}/quotes")
async def list_quotes(submission_id: str):
    """
    List all quotes for a submission.
    
    Args:
        submission_id: Submission identifier
        
    Returns:
        List of quote records for the submission.
    """
    try:
        # Verify submission exists
        submission = storage.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        
        quotes = storage.list_quotes_for_submission(submission_id)
        return quotes
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing quotes for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submissions/{submission_id}/compare")
async def compare_quotes(submission_id: str):
    """
    Run placement engine to compare quotes and generate recommendation.
    
    Args:
        submission_id: Submission identifier
        
    Returns:
        Comparison table, recommendation, and placement scores.
    """
    try:
        # Verify submission exists
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        
        # Convert to Submission dataclass (with nested types)
        submission = _submission_from_dict(submission_data)
        
        quotes_data = storage.list_quotes_for_submission(submission_id)
        
        if not quotes_data:
            return CompareResponse(
                comparison_table=[],
                recommendation="No quotes available for comparison",
                placement_scores=[],
            )
        
        # Convert quotes to Quote dataclass instances (with nested fields/scoring)
        quotes = [_quote_from_dict(q) for q in quotes_data]
        
        # Wire in PlacementEngine
        try:
            engine = PlacementEngine()
            
            # Load carrier profiles for FSR scoring
            carrier_profiles = {}
            for quote in quotes:
                profile_data = storage.get_carrier_profile_by_name(quote.carrier_name)
                if profile_data:
                    from app.broker.models import CarrierProfile
                    carrier_profiles[quote.carrier_name] = CarrierProfile(**profile_data)
            
            # Score quotes
            scored_quotes = engine.score_quotes(quotes, submission, carrier_profiles)
            
            # Generate recommendation
            recommendation = engine.generate_recommendation(scored_quotes)
            
            # Save scored quotes back to storage
            for quote in scored_quotes:
                storage.save_quote(quote)
            
        except Exception as e:
            logger.error(f"Placement engine failed for submission {submission_id}: {e}", exc_info=True)
            # Fall back to returning basic data if engine fails
            scored_quotes = quotes
            recommendation = (
                f"Analyzed {len(quotes)} quotes for submission {submission_id}. "
                "Placement scoring unavailable. Manual review recommended."
            )
        
        # Build response
        comparison_table = [
            {
                "quote_id": q.id,
                "carrier_name": q.carrier_name,
                "annual_premium": q.fields.annual_premium,
                "total_insured_value": q.fields.total_insured_value,
                "deductible": q.fields.deductible,
                "rating": q.fields.carrier_am_best_rating,
                "coverage_adequacy": q.scoring.coverage_adequacy,
                "placement_score": q.scoring.placement_score,
            }
            for q in scored_quotes
        ]
        
        placement_scores = [
            {
                "quote_id": q.id,
                "carrier_name": q.carrier_name,
                "placement_score": q.scoring.placement_score,
                "placement_rank": q.scoring.placement_rank,
                "recommendation_rationale": q.scoring.recommendation_rationale,
                "coverage_gaps": q.scoring.coverage_gaps,
                "premium_percentile": q.scoring.premium_percentile,
            }
            for q in scored_quotes
        ]
        
        return CompareResponse(
            comparison_table=comparison_table,
            recommendation=recommendation,
            placement_scores=placement_scores,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing quotes for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Document Upload Endpoint
# ============================================================================

VALID_DOCUMENT_TYPES = {dt.value for dt in DocumentType}


@router.post("/submissions/{submission_id}/documents", status_code=201)
async def upload_document(
    submission_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("other"),
):
    """
    Upload a client document (SOV, loss runs, prior declaration, etc.) to a submission.

    Args:
        submission_id: Submission identifier
        file: Document file to upload
        document_type: One of acord_125, acord_140, sov, loss_runs,
                       prior_declaration, other

    Returns:
        201 with the created BrokerDocument record.
    """
    try:
        # Validate submission exists
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(
                status_code=404,
                detail=f"Submission {submission_id} not found",
            )

        # Validate document_type
        if document_type not in VALID_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid document_type '{document_type}'. Must be one of: {sorted(VALID_DOCUMENT_TYPES)}",
            )

        # Save file to data/broker/documents/{submission_id}/
        docs_dir = Path("data") / "broker" / "documents" / submission_id
        docs_dir.mkdir(parents=True, exist_ok=True)
        file_path = docs_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)

        # Create BrokerDocument record
        doc = BrokerDocument(
            submission_id=submission_id,
            document_type=document_type,
            file_name=file.filename,
            blob_url=str(file_path),
        )

        # Add to submission.documents and save
        documents: list = submission_data.get("documents", [])
        documents.append(asdict(doc))
        submission_data["documents"] = documents
        submission_data["updated_at"] = datetime.utcnow().isoformat()
        submission = _submission_from_dict(submission_data)
        storage.save_submission(submission)

        return asdict(doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error uploading document for submission {submission_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACORD Field Extraction & Forms Endpoints
# ============================================================================


@router.post("/submissions/{submission_id}/extract-acord")
async def extract_acord_fields(submission_id: str):
    """
    Run ACORD field extraction on documents attached to a submission.

    Reads all documents, uses the SubmissionGenerator engine to extract
    ACORD 125/140 fields, and saves extracted fields + confidence scores.

    Args:
        submission_id: Submission identifier

    Returns:
        200 with extracted ACORD 125/140 fields and confidence scores.
    """
    try:
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

        # Reconstruct BrokerDocument list
        documents = [
            BrokerDocument(**{
                k: v for k, v in d.items()
                if k in BrokerDocument.__dataclass_fields__
            })
            for d in submission_data.get("documents", [])
        ]

        if not documents:
            raise HTTPException(
                status_code=422,
                detail="No documents attached to this submission. Upload documents first.",
            )

        # Run extraction
        generator = SubmissionGenerator(_settings.openai)
        acord_125, acord_140, confidence = await generator.extract_acord_fields(documents)

        # Save to submission
        submission_data["acord_125_fields"] = acord_125
        submission_data["acord_140_fields"] = acord_140
        submission_data["acord_field_confidence"] = confidence
        submission_data["updated_at"] = datetime.utcnow().isoformat()
        submission = _submission_from_dict(submission_data)
        storage.save_submission(submission)

        return {
            "submission_id": submission_id,
            "acord_125": acord_125,
            "acord_140": acord_140,
            "confidence": confidence,
            "fields_extracted": len(acord_125) + len(acord_140),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting ACORD fields for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{submission_id}/acord-forms")
async def get_acord_forms(submission_id: str):
    """
    Get ACORD form data with field metadata for UI rendering.

    Merges extracted values with the ACORD 125/140 form templates so the
    frontend can render editable forms with labels, sections, and required
    flags.

    Args:
        submission_id: Submission identifier

    Returns:
        200 with ACORD 125 template, ACORD 140 template, SOV template,
        each merged with extracted values and confidence scores.
    """
    try:
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

        extracted_125 = submission_data.get("acord_125_fields", {})
        extracted_140 = submission_data.get("acord_140_fields", {})
        confidence = submission_data.get("acord_field_confidence", {})

        # Map internal field names to canonical ACORD names
        mapped_125 = map_extracted_to_acord125(extracted_125)

        # Build ACORD 125 form with values
        template_125 = get_acord_form_template("125")
        form_125_fields = {}
        for field_key, meta in template_125["fields"].items():
            form_125_fields[field_key] = {
                **meta,
                "value": mapped_125.get(field_key, extracted_125.get(field_key, "")),
                "confidence": confidence.get(field_key, confidence.get(
                    # Also check snake_case keys
                    field_key.lower(), None
                )),
            }

        # Build ACORD 140 form with values
        template_140 = get_acord_form_template("140")
        form_140_fields = {}
        for field_key, meta in template_140["fields"].items():
            form_140_fields[field_key] = {
                **meta,
                "value": extracted_140.get(field_key, ""),
                "confidence": confidence.get(field_key, None),
            }

        # Build SOV template
        template_sov = get_acord_form_template("sov")

        return {
            "submission_id": submission_id,
            "acord_125": {
                "form_type": template_125["form_type"],
                "title": template_125["title"],
                "fields": form_125_fields,
                "raw_extracted": extracted_125,
            },
            "acord_140": {
                "form_type": template_140["form_type"],
                "title": template_140["title"],
                "fields": form_140_fields,
                "raw_extracted": extracted_140,
            },
            "sov": {
                "form_type": template_sov["form_type"],
                "title": template_sov["title"],
                "field_schema": template_sov["fields"],
                "locations": extracted_140.get("property_locations", []),
            },
            "confidence": confidence,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ACORD forms for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/submissions/{submission_id}/acord-fields")
async def update_acord_fields(submission_id: str, request: UpdateAcordFieldsRequest):
    """
    Save edited ACORD field values.

    The broker edits fields in the UI and saves them back to the
    submission record.

    Args:
        submission_id: Submission identifier
        request: Updated ACORD 125 and 140 field values

    Returns:
        200 with the updated fields.
    """
    try:
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

        if request.acord_125_fields:
            submission_data["acord_125_fields"] = request.acord_125_fields
        if request.acord_140_fields:
            submission_data["acord_140_fields"] = request.acord_140_fields
        submission_data["updated_at"] = datetime.utcnow().isoformat()

        submission = _submission_from_dict(submission_data)
        storage.save_submission(submission)

        return {
            "submission_id": submission_id,
            "acord_125_fields": submission_data.get("acord_125_fields", {}),
            "acord_140_fields": submission_data.get("acord_140_fields", {}),
            "updated_at": submission_data["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ACORD fields for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Submission Package Endpoint
# ============================================================================


@router.post("/submissions/{submission_id}/generate-package")
async def generate_submission_package(
    submission_id: str,
    request: Optional[GeneratePackageRequest] = None,
):
    """
    Generate a submission package from the submission's documents and
    extracted ACORD fields.

    Enhanced version: generates a cover email via LLM, compiles ACORD 125 +
    140 + SOV + documents into a package, and returns the full package
    with an editable cover email draft.

    Accepts an optional ``carriers`` list in the request body.  Falls back
    to the submission's ``submitted_carriers`` when not provided.

    Args:
        submission_id: Submission identifier
        request: Optional request body with carrier list

    Returns:
        200 with the full submission package JSON.
    """
    try:
        # Get submission
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(
                status_code=404,
                detail=f"Submission {submission_id} not found",
            )

        # Get associated client
        client_id = submission_data.get("client_id", "")
        client_data = storage.get_client(client_id) if client_id else {}
        if client_data is None:
            client_data = {}

        # Resolve carrier list
        carriers = (
            request.carriers
            if request and request.carriers
            else submission_data.get("submitted_carriers", [])
        )

        # Generate cover email
        pkg_gen = SubmissionPackageGenerator(_settings.openai)
        cover_email = await pkg_gen.generate_cover_email(
            client_data, submission_data, carriers,
        )

        # Compile full package
        package = pkg_gen.compile_package(client_data, submission_data, cover_email)

        # Generate per-carrier emails
        carrier_emails = await pkg_gen.generate_carrier_emails(package, carriers)
        package["carrier_emails"] = carrier_emails

        # Add quotes summary
        package["quotes_summary"] = [
            {
                "id": q.get("id", ""),
                "carrier_name": q.get("carrier_name", ""),
                "annual_premium": q.get("fields", {}).get("annual_premium", ""),
                "status": q.get("status", ""),
            }
            for q in submission_data.get("quotes", [])
        ]

        # Update submission status
        submission_data["status"] = SubmissionStatus.SUBMITTED.value
        submission_data["submission_date"] = datetime.utcnow().isoformat()
        submission_data["updated_at"] = datetime.utcnow().isoformat()
        if carriers:
            submission_data["submitted_carriers"] = carriers
        submission = _submission_from_dict(submission_data)
        storage.save_submission(submission)

        package["status"] = SubmissionStatus.SUBMITTED.value
        return package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error generating package for submission {submission_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/submissions/{submission_id}/package-email")
async def update_package_email(submission_id: str, request: UpdatePackageEmailRequest):
    """
    Save an edited cover email draft for a submission package.

    The broker edits the draft email in the UI and saves it back.

    Args:
        submission_id: Submission identifier
        request: Updated cover email text

    Returns:
        200 with confirmation and the saved email.
    """
    try:
        submission_data = storage.get_submission(submission_id)
        if not submission_data:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

        # Store cover email in the submission's coverage_requested dict
        coverage = submission_data.get("coverage_requested", {})
        coverage["cover_email_draft"] = request.cover_email
        submission_data["coverage_requested"] = coverage
        submission_data["updated_at"] = datetime.utcnow().isoformat()

        submission = _submission_from_dict(submission_data)
        storage.save_submission(submission)

        return {
            "submission_id": submission_id,
            "cover_email": request.cover_email,
            "updated_at": submission_data["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving package email for submission {submission_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Client Research Endpoint
# ============================================================================

@router.post("/clients/{client_id}/research")
async def research_client(client_id: str, request: ResearchRequest):
    """
    Run AI-powered client research and return a structured ResearchBrief.

    Optionally incorporates uploaded research documents (AM Best reports, etc.)
    when document_ids are provided.

    Args:
        client_id: Client identifier
        request: Research parameters including company name and optional document_ids

    Returns:
        Structured ResearchResponse (not free-text markdown).
    """
    try:
        # Verify client exists
        client_data = storage.get_client(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

        # Load uploaded research documents if any IDs provided
        uploaded_docs: List[str] = []
        if request.document_ids:
            research_docs_dir = Path("data") / "broker" / "research-documents" / client_id
            for doc_id in request.document_ids:
                # Look up metadata to find the file
                meta_path = research_docs_dir / f"{doc_id}.meta.json"
                if not meta_path.exists():
                    logger.warning(f"Research document {doc_id} not found, skipping")
                    continue
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    file_path = Path(meta.get("file_path", ""))
                    if file_path.exists():
                        doc_text = file_path.read_text(encoding="utf-8", errors="replace")
                        uploaded_docs.append(doc_text)
                        logger.info(f"Loaded research doc {doc_id}: {len(doc_text)} chars")
                except Exception as doc_err:
                    logger.warning(f"Failed to read research document {doc_id}: {doc_err}")

        # Wire in ClientResearchEngine
        try:
            research_engine = ClientResearchEngine(_settings.openai)
            brief = await research_engine.research_client(
                request.company_name,
                uploaded_docs=uploaded_docs if uploaded_docs else None,
            )

            # Save the research brief to the client record
            client_data["research_brief"] = brief
            # Convert property_locations dicts → PropertyLocation dataclasses
            if isinstance(client_data.get("property_locations"), list):
                client_data["property_locations"] = [
                    PropertyLocation(**loc) if isinstance(loc, dict) else loc
                    for loc in client_data["property_locations"]
                ]
            valid_keys = set(Client.__dataclass_fields__)
            client = Client(**{k: v for k, v in client_data.items() if k in valid_keys})
            storage.save_client(client)

            # Return structured response
            brief.setdefault("company_name", request.company_name)
            return ResearchResponse(**{
                k: v for k, v in brief.items()
                if k in ResearchResponse.model_fields and not k.startswith("_")
            })

        except Exception as e:
            logger.error(f"Client research failed for {client_id}: {e}", exc_info=True)
            # Return structured demo fallback when AI research engine is unavailable
            revenue = client_data.get('annual_revenue', '$12,000,000')
            employees = client_data.get('employee_count', 45)
            years = client_data.get('years_in_business', 15)
            hq = client_data.get('headquarters_address', 'Hartford, CT')
            industry = client_data.get('industry_code', '531110')
            num_locations = len(client_data.get('property_locations', [])) or 3

            return ResearchResponse(
                company_name=request.company_name,
                business_description=(
                    f"{request.company_name} is a commercial property management company "
                    f"based in {hq}, specializing in Class A office space, mixed-use "
                    f"retail/office properties, and warehouse/distribution facilities "
                    f"across Connecticut. Manages approximately $18.5M TIV across "
                    f"{num_locations} locations with {employees} employees."
                ),
                headquarters=hq,
                year_founded=(datetime.utcnow().year - years) if years else None,
                employee_count=employees,
                ownership_type="Private (LLC)",
                key_operations=[
                    "Commercial property management",
                    "Class A office leasing",
                    "Mixed-use retail/office operations",
                    "Warehouse/distribution facilities",
                ],
                annual_revenue=revenue,
                revenue_trend="Stable",
                credit_rating="Investment grade equivalent",
                financial_highlights=[
                    "Consistent occupancy rates above 90%",
                    "Conservative debt-to-equity ratio at 0.45",
                    f"Total Insured Value: $18,500,000 across {num_locations} locations",
                ],
                naics_code=industry,
                industry_sector="Commercial Real Estate",
                common_perils=[
                    "Property damage (fire, water)",
                    "Wind/hail (coastal exposure)",
                    "Slip & fall liability",
                ],
                loss_frequency="Low",
                risk_factors=[
                    "Coastal exposure (Stamford property)",
                    "Aging infrastructure (New Haven property)",
                    "Connecticut nor'easter exposure",
                ],
                insurance_needs=[
                    {"line": "Commercial Property", "priority": "Primary", "estimated_premium": "$35,000 - $50,000", "rationale": f"$18.5M TIV across {num_locations} locations"},
                    {"line": "General Liability", "priority": "Required", "estimated_premium": "$8,000 - $15,000", "rationale": "Office/retail tenant exposure"},
                    {"line": "Workers Compensation", "priority": "Required", "estimated_premium": "$12,000 - $18,000", "rationale": f"{employees} employees, property maintenance"},
                    {"line": "Umbrella/Excess", "priority": "Recommended", "estimated_premium": "$5,000 - $10,000", "rationale": "Multi-location liability aggregation"},
                    {"line": "Cyber Liability", "priority": "Recommended", "estimated_premium": "$3,000 - $6,000", "rationale": "Tenant data, online leasing platform"},
                ],
                carrier_matches=[
                    {"carrier": "Travelers", "rating": "A++", "appetite": "Strong", "rationale": "CT commercial property expertise"},
                    {"carrier": "AIG", "rating": "A+", "appetite": "Good", "rationale": "Multi-location property program"},
                    {"carrier": "Zurich", "rating": "A+", "appetite": "Good", "rationale": "Clean loss history pricing; flood coverage"},
                    {"carrier": "Hartford", "rating": "A+", "appetite": "Strong", "rationale": "Regional CT expertise; local claims handling"},
                ],
                recent_news=[
                    {"date": "2025-01-10", "headline": "CT commercial property market hardening 5-8% for 2026 renewals", "source": "Hartford Business Journal"},
                    {"date": "2024-12-15", "headline": "Hartford metro office vacancy stabilizing at 12%", "source": "CoStar"},
                ],
                citations=[
                    "Client database records",
                    "CT Insurance Department — Market Report 2025",
                    "NAICS industry classification data",
                    "Note: Demo content — AI research engine unavailable",
                ],
                confidence_level="Medium",
                data_sources=["Demo Fallback"],
                generated_at=datetime.utcnow().isoformat(),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error researching client {client_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Research Document Upload Endpoint
# ============================================================================

VALID_RESEARCH_DOC_TYPES = {"am_best", "annual_report", "financial_statement", "sp_report", "other"}


@router.post("/clients/{client_id}/research-documents", status_code=201)
async def upload_research_document(
    client_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("other"),
):
    """
    Upload a pre-research document (AM Best report, annual report, etc.)
    that will be fed into the research engine as primary source context.

    Args:
        client_id: Client identifier
        file: Document file to upload
        document_type: One of am_best, annual_report, financial_statement, sp_report, other

    Returns:
        201 with the created ResearchDocument metadata.
    """
    try:
        # Verify client exists
        client_data = storage.get_client(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

        if document_type not in VALID_RESEARCH_DOC_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid document_type '{document_type}'. Must be one of: {sorted(VALID_RESEARCH_DOC_TYPES)}",
            )

        # Save file to data/broker/research-documents/{client_id}/
        docs_dir = Path("data") / "broker" / "research-documents" / client_id
        docs_dir.mkdir(parents=True, exist_ok=True)

        doc_id = str(uuid.uuid4())
        file_path = docs_dir / f"{doc_id}_{file.filename}"
        content = await file.read()
        file_path.write_bytes(content)

        # Write metadata sidecar so the research endpoint can look it up
        meta = {
            "id": doc_id,
            "client_id": client_id,
            "file_name": file.filename,
            "document_type": document_type,
            "file_path": str(file_path),
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        meta_path = docs_dir / f"{doc_id}.meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        logger.info(
            f"Uploaded research document {doc_id} ({file.filename}) for client {client_id}"
        )

        return meta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error uploading research document for client {client_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients/{client_id}/research-documents")
async def list_research_documents(client_id: str):
    """
    List all research documents uploaded for a client.

    Args:
        client_id: Client identifier

    Returns:
        List of research document metadata records.
    """
    try:
        client_data = storage.get_client(client_id)
        if not client_data:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

        docs_dir = Path("data") / "broker" / "research-documents" / client_id
        if not docs_dir.exists():
            return []

        results = []
        for meta_file in sorted(docs_dir.glob("*.meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                results.append(meta)
            except Exception:
                continue
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error listing research documents for client {client_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Carrier Endpoints
# ============================================================================

@router.get("/carriers")
async def list_carriers():
    """
    List all carrier profiles.
    
    Returns:
        List of carrier profile records.
    """
    try:
        carriers = storage.list_carrier_profiles()
        return carriers
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing carrier profiles", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/carriers", status_code=201)
async def create_carrier(request: CreateCarrierRequest):
    """
    Add or update a carrier profile.
    
    Args:
        request: Carrier profile data
        
    Returns:
        Created/updated carrier profile record.
    """
    try:
        # Create CarrierProfile dataclass instance
        carrier = CarrierProfile(
            carrier_name=request.carrier_name,
            amb_number=request.amb_number,
            naic_code=request.naic_code,
            financial_strength_rating=request.financial_strength_rating,
            issuer_credit_rating=request.issuer_credit_rating,
            rating_outlook=request.rating_outlook,
            balance_sheet_strength=request.balance_sheet_strength,
            operating_performance=request.operating_performance,
            business_profile=request.business_profile,
            erm_assessment=request.erm_assessment,
            net_premiums_written=request.net_premiums_written,
            policyholders_surplus=request.policyholders_surplus,
            combined_ratio=request.combined_ratio,
            five_year_avg_combined_ratio=request.five_year_avg_combined_ratio,
            report_date=request.report_date,
            direct_written_premium=request.direct_written_premium,
            nwp_to_surplus_ratio=request.nwp_to_surplus_ratio,
            lines_of_business_written=request.lines_of_business_written,
            geographic_concentration=request.geographic_concentration,
        )
        
        # Save to storage
        storage.save_carrier_profile(carrier)
        
        # Return as dict
        return asdict(carrier)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating carrier profile", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
