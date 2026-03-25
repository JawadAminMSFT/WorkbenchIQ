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
    CarrierProfile,
    Client,
    Placement,
    PropertyLocation,
    Quote,
    QuoteFields,
    Submission,
)
from app.broker.storage import BrokerStorage

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/broker", tags=["Commercial Brokerage"])

# Initialize storage
storage = BrokerStorage()


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


class ResearchResponse(BaseModel):
    company_name: str
    brief: str
    sources: List[str] = Field(default_factory=list)


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
        
        # Create Client instance and save
        client = Client(**existing)
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
        submission = Submission(**existing)
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
        
        # Save to storage
        storage.save_quote(quote)
        
        return UploadQuoteResponse(
            quote_id=quote.id,
            status="uploaded",
            message=f"Quote from {carrier_name} uploaded successfully",
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
        submission = storage.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
        
        quotes = storage.list_quotes_for_submission(submission_id)
        
        # TODO: integrate placement engine
        # For now, return mock comparison data
        comparison_table = [
            {
                "quote_id": q.get("id", ""),
                "carrier_name": q.get("carrier_name", ""),
                "annual_premium": q.get("fields", {}).get("annual_premium", "$0"),
                "total_insured_value": q.get("fields", {}).get("total_insured_value", "$0"),
                "deductible": q.get("fields", {}).get("deductible", "$0"),
                "rating": q.get("fields", {}).get("carrier_am_best_rating", "N/A"),
                "coverage_adequacy": q.get("scoring", {}).get("coverage_adequacy", "adequate"),
                "placement_score": q.get("scoring", {}).get("placement_score", 0.0),
            }
            for q in quotes
        ]
        
        placement_scores = [
            {
                "quote_id": q.get("id", ""),
                "carrier_name": q.get("carrier_name", ""),
                "placement_score": q.get("scoring", {}).get("placement_score", 0.0),
                "placement_rank": q.get("scoring", {}).get("placement_rank", 0),
                "recommendation_rationale": q.get("scoring", {}).get("recommendation_rationale", ""),
                "coverage_gaps": q.get("scoring", {}).get("coverage_gaps", []),
                "premium_percentile": q.get("scoring", {}).get("premium_percentile", "market"),
            }
            for q in quotes
        ]
        
        recommendation = (
            f"Analyzed {len(quotes)} quotes for submission {submission_id}. "
            "Placement engine integration pending. "
            "Manual review recommended for final selection."
        )
        
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
# Client Research Endpoint
# ============================================================================

@router.post("/clients/{client_id}/research")
async def research_client(client_id: str, request: ResearchRequest):
    """
    Run AI-powered client research.
    
    Args:
        client_id: Client identifier
        request: Research parameters including company name
        
    Returns:
        AI-generated research brief with sources.
    """
    try:
        # Verify client exists
        client = storage.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        
        # TODO: integrate AI research engine
        # For now, return mock research data
        mock_brief = f"""
# Client Research Brief: {request.company_name}

## Business Overview
{request.company_name} is a commercial enterprise operating in the {client.get('industry_code', 'N/A')} sector.
Based in {client.get('headquarters_address', 'N/A')}, the company has been in business for 
{client.get('years_in_business', 'N/A')} years.

## Financial Profile
- Annual Revenue: {client.get('annual_revenue', 'N/A')}
- Employee Count: {client.get('employee_count', 'N/A')}
- Business Type: {client.get('business_type', 'N/A')}

## Risk Profile
Property locations: {len(client.get('property_locations', []))} locations on file.
Renewal date: {client.get('renewal_date', 'N/A')}

## Recommendations
- Review current coverage adequacy
- Assess risk management practices
- Evaluate carrier market appetite

*AI research engine integration pending.*
        """.strip()
        
        return ResearchResponse(
            company_name=request.company_name,
            brief=mock_brief,
            sources=[
                "Client database records",
                "Public business registry",
                "Industry reports (mock)",
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error researching client {client_id}", exc_info=True)
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
