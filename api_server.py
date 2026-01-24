"""
FastAPI backend server for the Underwriting Assistant.
This provides REST API endpoints for the Next.js frontend.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from app.config import load_settings, validate_settings
from app.database.settings import DatabaseSettings
from app.database.pool import init_pool
from app.storage import (
    list_applications,
    load_application,
    new_metadata,
    save_uploaded_files,
    save_application_metadata,
    ApplicationMetadata,
)
from app.processing import (
    run_content_understanding_for_files,
    run_underwriting_prompts,
)
from app.prompts import load_prompts, save_prompts
from app.content_understanding_client import (
    get_analyzer,
    create_or_update_custom_analyzer,
    delete_analyzer,
)
from app.config import UNDERWRITING_FIELD_SCHEMA
from app.personas import list_personas, get_persona_config, get_field_schema
from app.utils import setup_logging

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="WorkbenchIQ API",
    description="REST API for WorkbenchIQ - Multi-persona document processing workbench",
    version="0.3.0",
)

# Configure CORS for frontend access
# In production, replace with your actual frontend domain(s)
allowed_origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Add Azure frontend URL from environment variable if configured
import os
azure_frontend_url = os.getenv("FRONTEND_URL")
if azure_frontend_url:
    allowed_origins.append(azure_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers (lazy loading to avoid circular imports)
try:
    from app.claims.api import router as claims_api_router
    app.include_router(claims_api_router)
    logger.info("Claims API router registered")
except ImportError as e:
    logger.warning("Claims API router not available: %s", e)


# Initialize storage provider and database pool on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    from app.storage_providers import init_storage_provider, StorageSettings
    try:
        storage_settings = StorageSettings.from_env()
        init_storage_provider(storage_settings)
        logger.info("Storage provider initialized: %s", storage_settings.backend.value)
    except Exception as e:
        logger.error("Failed to initialize storage provider: %s", e)
        raise

    # Initialize database pool if using PostgreSQL
    settings = load_settings()
    if settings.database.backend == "postgresql":
        try:
            await init_pool(settings.database)
            logger.info("Database pool initialized (PostgreSQL)")
        except Exception as e:
            logger.error("Failed to initialize database pool: %s", e)
            raise


# Pydantic models for API responses
class ApplicationListItem(BaseModel):
    id: str
    created_at: Optional[str]
    external_reference: Optional[str]
    status: str
    persona: Optional[str] = None
    summary_title: Optional[str] = None
    processing_status: Optional[str] = None


class AnalyzeRequest(BaseModel):
    sections: Optional[List[str]] = None


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    application_id: Optional[str] = None
    conversation_id: Optional[str] = None  # If provided, continues existing conversation
    persona: Optional[str] = None  # Persona for RAG context (underwriting, life_health_claims, automotive_claims, property_casualty_claims)


class ConversationSummary(BaseModel):
    id: str
    application_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    preview: Optional[str] = None


class Conversation(BaseModel):
    id: str
    application_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage]


def application_to_dict(app_md: ApplicationMetadata) -> dict:
    """Convert ApplicationMetadata to JSON-serializable dict."""
    return {
        "id": app_md.id,
        "created_at": app_md.created_at,
        "external_reference": app_md.external_reference,
        "status": app_md.status,
        "persona": app_md.persona,
        "files": [
            {"filename": f.filename, "path": f.path, "url": f.url}
            for f in app_md.files
        ],
        "document_markdown": app_md.document_markdown,
        "markdown_pages": app_md.markdown_pages,
        "cu_raw_result_path": app_md.cu_raw_result_path,
        "llm_outputs": app_md.llm_outputs,
        "extracted_fields": app_md.extracted_fields,
        "confidence_summary": app_md.confidence_summary,
        "analyzer_id_used": app_md.analyzer_id_used,
        "risk_analysis": app_md.risk_analysis,
        "processing_status": app_md.processing_status,
        "processing_error": app_md.processing_error,
    }


# ============================================================================
# Background Processing Helpers
# ============================================================================

def _handle_task_exception(task: asyncio.Task):
    """Callback to log exceptions from background tasks."""
    try:
        exc = task.exception()
        if exc:
            logger.error("Background task failed with exception: %s", exc, exc_info=exc)
    except asyncio.CancelledError:
        pass


async def run_extraction_background(app_id: str):
    """Run content extraction in background and update status."""
    try:
        logger.info("Starting background extraction for application %s", app_id)
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            logger.error("Background extraction: Application %s not found", app_id)
            return

        # Update status to extracting
        app_md.processing_status = "extracting"
        app_md.processing_error = None
        save_application_metadata(settings.app.storage_root, app_md)

        # Run extraction in thread pool
        logger.info("Running content understanding for application %s", app_id)
        app_md = await asyncio.to_thread(
            run_content_understanding_for_files, settings, app_md
        )
        
        # Update status and save
        app_md.processing_status = None
        app_md.processing_error = None
        save_application_metadata(settings.app.storage_root, app_md)
        
        logger.info("Background extraction completed for application %s", app_id)

    except Exception as e:
        logger.error("Background extraction failed for %s: %s", app_id, e, exc_info=True)
        try:
            settings = load_settings()
            app_md = load_application(settings.app.storage_root, app_id)
            if app_md:
                app_md.processing_status = "error"
                app_md.processing_error = str(e)
                save_application_metadata(settings.app.storage_root, app_md)
        except Exception:
            pass


async def run_analysis_background(app_id: str, sections: Optional[List[str]] = None):
    """Run analysis in background and update status."""
    try:
        logger.info("Starting background analysis for application %s", app_id)
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            logger.error("Background analysis: Application %s not found", app_id)
            return

        # Update status to analyzing
        app_md.processing_status = "analyzing"
        app_md.processing_error = None
        save_application_metadata(settings.app.storage_root, app_md)

        # Run analysis in thread pool
        logger.info("Running underwriting prompts for application %s", app_id)
        app_md = await asyncio.to_thread(
            run_underwriting_prompts,
            settings,
            app_md,
            sections_to_run=sections,
            max_workers_per_section=4,
        )
        
        # Update status and save
        app_md.processing_status = None
        app_md.processing_error = None
        save_application_metadata(settings.app.storage_root, app_md)
        
        logger.info("Background analysis completed for application %s", app_id)

    except Exception as e:
        logger.error("Background analysis failed for %s: %s", app_id, e, exc_info=True)
        try:
            settings = load_settings()
            app_md = load_application(settings.app.storage_root, app_id)
            if app_md:
                app_md.processing_status = "error"
                app_md.processing_error = str(e)
                save_application_metadata(settings.app.storage_root, app_md)
        except Exception:
            pass


async def run_extract_and_analyze_background(app_id: str):
    """Run both extraction and analysis in background."""
    logger.info("Starting full background processing for application %s", app_id)
    await run_extraction_background(app_id)
    
    # Check if extraction succeeded before continuing
    settings = load_settings()
    app_md = load_application(settings.app.storage_root, app_id)
    if app_md and app_md.processing_status != "error" and app_md.document_markdown:
        await run_analysis_background(app_id)
    else:
        logger.warning("Skipping analysis for %s - extraction failed or no content", app_id)


# =============================================================================
# Persona-Aware Chat Prompts
# =============================================================================

PERSONA_CHAT_CONFIG = {
    "underwriting": {
        "role": "expert life insurance underwriter assistant",
        "context_type": "underwriting policies",
        "item_type": "application",
        "decision_type": "underwriting decisions",
        "example_policy_id": "CVD-BP-001",
    },
    "life_health_claims": {
        "role": "expert life and health insurance claims analyst",
        "context_type": "claims processing policies",
        "item_type": "claim",
        "decision_type": "claims processing decisions",
        "example_policy_id": "HC-COV-001",
    },
    "automotive_claims": {
        "role": "expert automotive insurance claims analyst",
        "context_type": "auto claims policies",
        "item_type": "claim",
        "decision_type": "claims processing decisions",
        "example_policy_id": "DMG-SEV-001",
    },
    "property_casualty_claims": {
        "role": "expert property and casualty claims analyst",
        "context_type": "property & casualty policies",
        "item_type": "claim",
        "decision_type": "claims processing decisions",
        "example_policy_id": "PC-COV-001",
    },
}


def get_chat_system_prompt(
    persona: str,
    policies_context: str,
    app_id: str,
    app_context_parts: list[str],
) -> str:
    """
    Generate a persona-aware system prompt for Ask IQ chat.
    
    Args:
        persona: The current persona type
        policies_context: RAG-retrieved or fallback policy context
        app_id: The application/claim ID
        app_context_parts: Parts of the application context to include
        
    Returns:
        System prompt string for the LLM
    """
    config = PERSONA_CHAT_CONFIG.get(persona, PERSONA_CHAT_CONFIG["underwriting"])
    
    return f"""You are an {config['role']}. You have access to the following context:

{policies_context}

## {config['item_type'].title()} Information (ID: {app_id})

{chr(10).join(app_context_parts) if app_context_parts else f"No {config['item_type']} details available yet."}

---

## Response Format Instructions:

When appropriate, structure your response as JSON to enable rich UI rendering. Use these formats:

### For risk factor summaries (when asked about risks, key factors, concerns):
```json
{{{{
  "type": "risk_factors",
  "summary": "Brief overall summary",
  "factors": [
    {{{{
      "title": "Factor name",
      "description": "Details about the factor",
      "risk_level": "low|moderate|high",
      "policy_id": "Optional policy ID like {config['example_policy_id']}"
    }}}}
  ],
  "overall_risk": "low|low-moderate|moderate|moderate-high|high"
}}}}
```

### For policy citations (when explaining which policies apply):
```json
{{{{
  "type": "policy_list",
  "summary": "Brief intro",
  "policies": [
    {{{{
      "policy_id": "{config['example_policy_id']}",
      "name": "Policy name",
      "relevance": "Why this policy applies",
      "finding": "What the policy evaluation found"
    }}}}
  ]
}}}}
```

### For recommendations (when asked about approval, action, decision):
```json
{{{{
  "type": "recommendation",
  "decision": "approve|approve_with_conditions|defer|decline",
  "confidence": "high|medium|low",
  "summary": "Brief recommendation summary",
  "conditions": ["List of conditions if applicable"],
  "rationale": "Detailed reasoning",
  "next_steps": ["Suggested next steps"]
}}}}
```

### For comparisons or tables:
```json
{{{{
  "type": "comparison",
  "title": "Comparison title",
  "columns": ["Column1", "Column2", "Column3"],
  "rows": [
    {{{{"label": "Row label", "values": ["val1", "val2", "val3"]}}}}
  ]
}}}}
```

For simple conversational responses or when structured format doesn't apply, respond with plain text.
Always wrap JSON responses in ```json code blocks.

## General Instructions:
1. Answer questions about this specific {config['item_type']} and the {config['context_type']}.
2. **IMPORTANT: Only reference policy IDs that appear in the policy context above.** Do not invent or guess policy IDs. Use exact IDs like {config['example_policy_id']} from the provided policies.
3. Provide clear, actionable guidance for {config['decision_type']}.
4. If you need more information to answer a question, ask for it.
5. Use structured JSON formats when they enhance clarity; use plain text for simple answers.
6. If no relevant policy exists for a topic, say so rather than inventing a policy ID.
"""


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.3.0", "name": "WorkbenchIQ"}


# ============================================================================
# Persona APIs
# ============================================================================

@app.get("/api/personas")
async def get_personas():
    """List all available personas."""
    try:
        personas = list_personas()
        return {"personas": personas}
    except Exception as e:
        logger.error("Failed to list personas: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/personas/{persona_id}")
async def get_persona(persona_id: str):
    """Get configuration for a specific persona."""
    try:
        config = get_persona_config(persona_id)
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "icon": config.icon,
            "color": config.color,
            "enabled": config.enabled,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get persona %s: %s", persona_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications", response_model=List[ApplicationListItem])
async def get_applications(persona: Optional[str] = None):
    """List all applications, optionally filtered by persona."""
    try:
        settings = load_settings()
        apps = list_applications(settings.app.storage_root, persona=persona)
        return [
            ApplicationListItem(
                id=a["id"],
                created_at=a.get("created_at"),
                external_reference=a.get("external_reference"),
                status=a.get("status", "unknown"),
                persona=a.get("persona"),
                summary_title=a.get("summary_title"),
                processing_status=a.get("processing_status"),
            )
            for a in apps
        ]
    except Exception as e:
        logger.error("Failed to list applications: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{app_id}")
async def get_application(app_id: str):
    """Get detailed application metadata."""
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")
        return application_to_dict(app_md)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to load application %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{app_id}/files/{filename:path}")
async def get_application_file(app_id: str, filename: str):
    """Serve a file from an application's files directory."""
    try:
        settings = load_settings()
        app_dir = Path(settings.app.storage_root) / "applications" / app_id / "files"
        file_path = app_dir / filename
        
        # Security: ensure the file is within the application directory
        try:
            file_path.resolve().relative_to(app_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine media type
        suffix = file_path.suffix.lower()
        media_types = {
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
        media_type = media_types.get(suffix, "application/octet-stream")
        
        # For PDFs, allow inline viewing in iframes/object tags
        headers = {}
        if suffix == ".pdf":
            headers["Content-Disposition"] = f"inline; filename=\"{filename}\""
            headers["X-Content-Type-Options"] = "nosniff"
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers=headers if headers else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to serve file %s for app %s: %s", filename, app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications")
async def create_application(
    files: List[UploadFile] = File(...),
    external_reference: Optional[str] = Form(None),
    persona: Optional[str] = Form(None),
):
    """Create a new application with uploaded PDF files."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        settings = load_settings()
        app_id = str(uuid.uuid4())[:8]

        # Read file contents asynchronously before passing to sync storage function
        file_data = []
        for f in files:
            content = await f.read()
            file_data.append({"name": f.filename, "content": content})

        # Save uploaded files
        stored_files = save_uploaded_files(
            settings.app.storage_root,
            app_id,
            file_data,
            public_base_url=settings.app.public_files_base_url,
        )

        # Create metadata with persona
        app_md = new_metadata(
            settings.app.storage_root,
            app_id,
            stored_files,
            external_reference=external_reference,
            persona=persona or "underwriting",  # Default to underwriting for backward compat
        )

        logger.info("Created application %s with %d files for persona %s", app_id, len(files), persona)
        return application_to_dict(app_md)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create application: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/extract")
async def extract_content(app_id: str, background: bool = False):
    """Run Content Understanding extraction on an application.
    
    Args:
        app_id: Application ID
        background: If True, start extraction in background and return immediately.
                   Client should poll GET /api/applications/{app_id} for status.
    """
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        if background:
            # Check if already processing
            if app_md.processing_status in ("extracting", "analyzing"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Application is already being processed: {app_md.processing_status}"
                )
            
            # Start background task and return immediately
            task = asyncio.create_task(run_extraction_background(app_id))
            task.add_done_callback(_handle_task_exception)
            
            # Update status immediately so client sees it
            app_md.processing_status = "extracting"
            app_md.processing_error = None
            save_application_metadata(settings.app.storage_root, app_md)
            
            logger.info("Started background extraction for application %s", app_id)
            return {
                **application_to_dict(app_md),
                "message": "Extraction started in background. Poll GET /api/applications/{app_id} for status."
            }
        
        # Synchronous mode (backward compatible)
        # Run content understanding in thread pool to avoid blocking event loop
        app_md = await asyncio.to_thread(
            run_content_understanding_for_files, settings, app_md
        )
        
        logger.info("Extraction completed for application %s", app_id)
        return application_to_dict(app_md)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Extraction failed for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/analyze")
async def analyze_application(app_id: str, request: AnalyzeRequest = None, background: bool = False):
    """Run underwriting prompts analysis on an application.
    
    Args:
        app_id: Application ID
        request: Optional request with sections to analyze
        background: If True, start analysis in background and return immediately.
                   Client should poll GET /api/applications/{app_id} for status.
    """
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        if not app_md.document_markdown:
            raise HTTPException(
                status_code=400,
                detail="No document content. Run extraction first."
            )

        sections_to_run = request.sections if request else None

        if background:
            # Check if already processing
            if app_md.processing_status in ("extracting", "analyzing"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Application is already being processed: {app_md.processing_status}"
                )
            
            # Start background task and return immediately
            task = asyncio.create_task(run_analysis_background(app_id, sections_to_run))
            task.add_done_callback(_handle_task_exception)
            
            # Update status immediately so client sees it
            app_md.processing_status = "analyzing"
            app_md.processing_error = None
            save_application_metadata(settings.app.storage_root, app_md)
            
            logger.info("Started background analysis for application %s", app_id)
            return {
                **application_to_dict(app_md),
                "message": "Analysis started in background. Poll GET /api/applications/{app_id} for status."
            }

        # Synchronous mode (backward compatible)
        # Run underwriting prompts in thread pool to avoid blocking event loop
        app_md = await asyncio.to_thread(
            run_underwriting_prompts,
            settings,
            app_md,
            sections_to_run=sections_to_run,
            max_workers_per_section=4,
        )

        logger.info("Analysis completed for application %s", app_id)
        return application_to_dict(app_md)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analysis failed for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/process")
async def process_application(app_id: str):
    """Start full processing (extraction + analysis) in background.
    
    This is the recommended endpoint for new uploads. It starts both
    extraction and analysis as background tasks and returns immediately.
    Client should poll GET /api/applications/{app_id} to check status.
    
    The processing_status field will be:
    - 'extracting': Currently running content extraction
    - 'analyzing': Extraction done, running analysis
    - null: Processing complete
    - 'error': Processing failed (check processing_error for details)
    """
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        # Check if already processing
        if app_md.processing_status in ("extracting", "analyzing"):
            raise HTTPException(
                status_code=409,
                detail=f"Application is already being processed: {app_md.processing_status}"
            )
        
        # Start background task for full processing
        task = asyncio.create_task(run_extract_and_analyze_background(app_id))
        task.add_done_callback(_handle_task_exception)
        
        # Update status immediately so client sees it
        app_md.processing_status = "extracting"
        app_md.processing_error = None
        save_application_metadata(settings.app.storage_root, app_md)
        
        logger.info("Started background processing for application %s", app_id)
        return {
            **application_to_dict(app_md),
            "message": "Processing started in background. Poll GET /api/applications/{app_id} for status."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start processing for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/risk-analysis")
async def run_application_risk_analysis(app_id: str):
    """Run policy-based risk analysis on an already-analyzed application.
    
    This is a separate operation from extraction/summarization.
    It applies underwriting policies to the extracted data and generates
    a comprehensive risk assessment with policy citations.
    
    Prerequisites:
    - Application must have completed extraction and analysis
    - LLM outputs must be present
    """
    from app.processing import run_risk_analysis
    
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        if not app_md.llm_outputs:
            raise HTTPException(
                status_code=400,
                detail="No analysis outputs found. Run standard analysis first."
            )
        
        if app_md.persona != "underwriting":
            raise HTTPException(
                status_code=400,
                detail="Risk analysis is only available for underwriting applications."
            )

        # Run risk analysis in thread pool to avoid blocking event loop
        risk_result = await asyncio.to_thread(
            run_risk_analysis, settings, app_md
        )
        
        logger.info("Risk analysis completed for application %s", app_id)
        return {
            "application_id": app_id,
            "risk_analysis": risk_result,
            "message": "Risk analysis completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Risk analysis failed for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{app_id}/risk-analysis")
async def get_application_risk_analysis(app_id: str):
    """Get the risk analysis results for an application."""
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        if not app_md.risk_analysis:
            raise HTTPException(
                status_code=404,
                detail="No risk analysis found. Run risk analysis first."
            )

        return {
            "application_id": app_id,
            "risk_analysis": app_md.risk_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get risk analysis for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/status")
async def config_status():
    """Check configuration status."""
    try:
        settings = load_settings()
        errors = validate_settings(settings)
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
        }


# ============================================================================
# Prompt Catalog APIs
# ============================================================================

class PromptUpdateRequest(BaseModel):
    """Request model for updating a single prompt."""
    text: str


class PromptsUpdateRequest(BaseModel):
    """Request model for bulk prompt updates."""
    prompts: dict


@app.get("/api/prompts")
async def get_prompts(persona: str = "underwriting"):
    """Get all prompts organized by section and subsection for a persona."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.prompts_root, persona)
        return {"prompts": prompts, "persona": persona}
    except Exception as e:
        logger.error("Failed to load prompts: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/{section}/{subsection}")
async def get_prompt(section: str, subsection: str, persona: str = "underwriting"):
    """Get a specific prompt by section and subsection."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.prompts_root, persona)
        
        if section not in prompts:
            raise HTTPException(status_code=404, detail=f"Section '{section}' not found")
        if subsection not in prompts[section]:
            raise HTTPException(status_code=404, detail=f"Subsection '{subsection}' not found in section '{section}'")
        
        return {
            "section": section,
            "subsection": subsection,
            "text": prompts[section][subsection]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get prompt %s/%s: %s", section, subsection, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/prompts/{section}/{subsection}")
async def update_prompt(section: str, subsection: str, request: PromptUpdateRequest, persona: str = "underwriting"):
    """Update a specific prompt."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.prompts_root, persona)
        
        if section not in prompts:
            prompts[section] = {}
        
        prompts[section][subsection] = request.text
        save_prompts(settings.app.prompts_root, prompts, persona)
        
        logger.info("Updated prompt %s/%s for persona %s", section, subsection, persona)
        return {
            "section": section,
            "subsection": subsection,
            "text": request.text,
            "message": "Prompt updated successfully"
        }
    except Exception as e:
        logger.error("Failed to update prompt %s/%s: %s", section, subsection, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/prompts/{section}/{subsection}")
async def delete_prompt(section: str, subsection: str, persona: str = "underwriting"):
    """Delete a specific prompt (resets to default if available)."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.prompts_root, persona)
        
        if section in prompts and subsection in prompts[section]:
            del prompts[section][subsection]
            # Remove section if empty
            if not prompts[section]:
                del prompts[section]
            save_prompts(settings.app.prompts_root, prompts, persona)
            
        logger.info("Deleted prompt %s/%s for persona %s", section, subsection, persona)
        return {"message": f"Prompt {section}/{subsection} deleted"}
    except Exception as e:
        logger.error("Failed to delete prompt %s/%s: %s", section, subsection, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompts/{section}/{subsection}")
async def create_prompt(section: str, subsection: str, request: PromptUpdateRequest, persona: str = "underwriting"):
    """Create a new prompt."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.prompts_root, persona)
        
        if section not in prompts:
            prompts[section] = {}
        
        if subsection in prompts[section]:
            raise HTTPException(
                status_code=409, 
                detail=f"Prompt '{section}/{subsection}' already exists. Use PUT to update."
            )
        
        prompts[section][subsection] = request.text
        save_prompts(settings.app.prompts_root, prompts, persona)
        
        logger.info("Created prompt %s/%s for persona %s", section, subsection, persona)
        return {
            "section": section,
            "subsection": subsection,
            "text": request.text,
            "message": "Prompt created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create prompt %s/%s: %s", section, subsection, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Content Understanding Analyzer APIs
# ============================================================================

class AnalyzerCreateRequest(BaseModel):
    """Request model for creating a custom analyzer."""
    analyzer_id: Optional[str] = None
    persona: Optional[str] = None
    description: Optional[str] = "Custom analyzer for document extraction"
    media_type: Optional[str] = None  # "document", "image", or "video"


@app.get("/api/analyzer/status")
async def get_analyzer_status(persona: Optional[str] = "underwriting"):
    """Get the current status of the custom analyzer for the specified persona."""
    try:
        settings = load_settings()
        
        # Get persona-specific analyzer ID
        try:
            persona_config = get_persona_config(persona)
            custom_analyzer_id = persona_config.custom_analyzer_id
        except ValueError:
            # Fallback to default if persona not found
            custom_analyzer_id = settings.content_understanding.custom_analyzer_id
        
        try:
            analyzer = get_analyzer(settings.content_understanding, custom_analyzer_id)
            return {
                "analyzer_id": custom_analyzer_id,
                "exists": analyzer is not None,
                "analyzer": analyzer,
                "confidence_scoring_enabled": settings.content_understanding.enable_confidence_scores,
                "default_analyzer_id": settings.content_understanding.analyzer_id,
                "persona": persona,
            }
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as timeout_err:
            logger.warning("Timeout checking analyzer status for %s: %s", custom_analyzer_id, timeout_err)
            return {
                "analyzer_id": custom_analyzer_id,
                "exists": None,
                "analyzer": None,
                "confidence_scoring_enabled": settings.content_understanding.enable_confidence_scores,
                "default_analyzer_id": settings.content_understanding.analyzer_id,
                "persona": persona,
                "error": f"Request timeout ({timeout_err})",
            }
        except requests.exceptions.ConnectionError as conn_err:
            logger.warning("Connection error checking analyzer status: %s", conn_err)
            return {
                "analyzer_id": custom_analyzer_id,
                "exists": None,
                "analyzer": None,
                "confidence_scoring_enabled": settings.content_understanding.enable_confidence_scores,
                "default_analyzer_id": settings.content_understanding.analyzer_id,
                "persona": persona,
                "error": "Cannot connect to Azure Content Understanding service",
            }
    except Exception as e:
        logger.error("Failed to get analyzer status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyzer/schema")
async def get_analyzer_schema(persona: Optional[str] = "underwriting"):
    """Get the current field schema for the custom analyzer."""
    try:
        schema = get_field_schema(persona)
        return {
            "schema": schema,
            "field_count": len(schema.get("fields", {})),
            "persona": persona,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get analyzer schema: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyzer/create")
async def create_custom_analyzer(request: AnalyzerCreateRequest = None):
    """Create or update the custom analyzer for confidence-scored extraction."""
    try:
        settings = load_settings()
        persona_id = request.persona if request and request.persona else "underwriting"
        media_type = request.media_type if request and request.media_type else "document"
        
        # Get the analyzer_id from persona config if not explicitly provided
        if request and request.analyzer_id:
            analyzer_id = request.analyzer_id
        else:
            try:
                persona_config = get_persona_config(persona_id)
                # Select analyzer based on media type
                if media_type == "image" and persona_config.image_analyzer_id:
                    analyzer_id = persona_config.image_analyzer_id
                elif media_type == "video" and persona_config.video_analyzer_id:
                    analyzer_id = persona_config.video_analyzer_id
                else:
                    analyzer_id = persona_config.custom_analyzer_id
            except ValueError:
                # Fallback to default if persona not found
                analyzer_id = settings.content_understanding.custom_analyzer_id
        
        description = request.description if request and request.description else f"Custom {persona_id} {media_type} analyzer for extraction with confidence scores"
        
        result = create_or_update_custom_analyzer(
            settings.content_understanding,
            analyzer_id=analyzer_id,
            persona_id=persona_id,
            description=description,
            media_type=media_type,
        )
        
        logger.info("Created/updated custom %s analyzer: %s", media_type, analyzer_id)
        return {
            "message": f"Analyzer '{analyzer_id}' created/updated successfully",
            "analyzer_id": analyzer_id,
            "result": result,
        }
    except Exception as e:
        logger.error("Failed to create analyzer: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analyzer/{analyzer_id}")
async def delete_custom_analyzer(analyzer_id: str):
    """Delete a custom analyzer."""
    try:
        settings = load_settings()
        
        success = delete_analyzer(settings.content_understanding, analyzer_id)
        
        if success:
            logger.info("Deleted analyzer: %s", analyzer_id)
            return {"message": f"Analyzer '{analyzer_id}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Analyzer '{analyzer_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete analyzer %s: %s", analyzer_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyzer/list")
async def list_analyzers():
    """List available analyzers (custom and default)."""
    try:
        settings = load_settings()
        default_id = settings.content_understanding.analyzer_id
        
        analyzers = [
            {
                "id": default_id,
                "type": "prebuilt",
                "description": "Azure prebuilt document search analyzer",
                "exists": True,  # Prebuilt analyzers always exist
                "persona": None,
            },
        ]
        
        # Get all persona configurations
        personas = list_personas()
        
        # Helper function to check and add an analyzer
        def add_analyzer(analyzer_id: str, persona_id: str, persona_name: str, media_type: str = "document"):
            """Check if analyzer exists and add to list."""
            try:
                custom_analyzer = get_analyzer(settings.content_understanding, analyzer_id)
                if custom_analyzer:
                    analyzers.append({
                        "id": analyzer_id,
                        "type": "custom",
                        "media_type": media_type,
                        "description": custom_analyzer.get("description", f"Custom {persona_name} {media_type} analyzer"),
                        "exists": True,
                        "persona": persona_id,
                        "persona_name": persona_name,
                    })
                else:
                    analyzers.append({
                        "id": analyzer_id,
                        "type": "custom",
                        "media_type": media_type,
                        "description": f"Custom {persona_name} {media_type} analyzer (not created yet)",
                        "exists": False,
                        "persona": persona_id,
                        "persona_name": persona_name,
                    })
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as timeout_err:
                logger.warning("Timeout checking custom analyzer %s for persona %s: %s", analyzer_id, persona_id, timeout_err)
                analyzers.append({
                    "id": analyzer_id,
                    "type": "custom",
                    "media_type": media_type,
                    "description": f"Custom {persona_name} {media_type} analyzer (status unknown - timeout)",
                    "exists": None,
                    "persona": persona_id,
                    "persona_name": persona_name,
                    "error": f"Request timeout ({timeout_err})",
                })
            except requests.exceptions.ConnectionError as conn_err:
                logger.warning("Connection error checking custom analyzer %s for persona %s: %s", analyzer_id, persona_id, conn_err)
                analyzers.append({
                    "id": analyzer_id,
                    "type": "custom",
                    "media_type": media_type,
                    "description": f"Custom {persona_name} {media_type} analyzer (status unknown - connection error)",
                    "exists": None,
                    "persona": persona_id,
                    "persona_name": persona_name,
                    "error": "Cannot connect to Azure Content Understanding service",
                })
        
        # Check each persona's custom analyzers
        for persona in personas:
            if not persona.get("enabled", True):
                continue  # Skip disabled personas
                
            persona_id = persona["id"]
            try:
                persona_config = get_persona_config(persona_id)
                
                # Add document analyzer
                add_analyzer(persona_config.custom_analyzer_id, persona_id, persona["name"], "document")
                
                # Add image analyzer if configured (multimodal personas)
                if persona_config.image_analyzer_id:
                    add_analyzer(persona_config.image_analyzer_id, persona_id, persona["name"], "image")
                
                # Add video analyzer if configured (multimodal personas)
                if persona_config.video_analyzer_id:
                    add_analyzer(persona_config.video_analyzer_id, persona_id, persona["name"], "video")
                    
            except Exception as e:
                logger.warning("Error processing persona %s: %s", persona_id, e)
                continue
        
        return {"analyzers": analyzers}
    except Exception as e:
        logger.error("Failed to list analyzers: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Underwriting Policy Endpoints
# =============================================================================

@app.get("/api/policies")
async def get_policies(persona: str = "underwriting"):
    """Get policies for the specified persona.
    
    - For 'underwriting' persona: Returns underwriting policies from life-health-underwriting-policies.json
    - For 'automotive_claims' persona: Returns automotive claims policies from automotive-claims-policies.json
    - For other claims personas (life_health_claims, property_casualty_claims): Returns claims/health plan policies from policies.json
    """
    from app.underwriting_policies import load_policies as load_underwriting_policies
    from app.processing import load_policies as load_claims_policies
    
    try:
        settings = load_settings()
        
        # Special handling for automotive claims
        if persona == "automotive_claims":
            from app.claims.policies import ClaimsPolicyLoader
            loader = ClaimsPolicyLoader()
            loader.load_policies("data/automotive-claims-policies.json")
            policies = [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "subcategory": p.subcategory,
                    "description": p.description,
                    "criteria": [
                        {
                            "id": c.id,
                            "condition": c.condition,
                            "severity": c.severity,
                            "action": c.action,
                            "rationale": c.rationale,
                        }
                        for c in p.criteria
                    ],
                    "modifying_factors": [
                        {"factor": mf.factor, "impact": mf.impact}
                        for mf in p.modifying_factors
                    ],
                    "references": p.references,
                }
                for p in loader.get_all_policies()
            ]
            return {
                "policies": policies,
                "total": len(policies),
                "persona": persona,
                "type": "automotive_claims",
            }
        
        # Check if this is a claims persona (life_health_claims, property_casualty_claims, etc.)
        is_claims_persona = "claims" in persona.lower()
        
        if is_claims_persona:
            # Load claims policies (health plans with coverage info)
            policies_data = load_claims_policies(settings.app.prompts_root)
            # Convert dict format to list format for consistency
            policies = [
                {"id": plan_name, "name": plan_name, **plan_data}
                for plan_name, plan_data in policies_data.items()
            ]
            return {
                "policies": policies,
                "total": len(policies),
                "persona": persona,
                "type": "claims",
            }
        else:
            # Load underwriting policies (risk assessment criteria)
            policies_data = load_underwriting_policies(settings.app.prompts_root)
            policies = policies_data.get("policies", [])
            return {
                "policies": policies,
                "total": len(policies),
                "persona": persona,
                "type": "underwriting",
            }
    except Exception as e:
        logger.error("Failed to get policies for persona %s: %s", persona, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/{policy_id}")
async def get_policy_by_id(policy_id: str, persona: str = "underwriting"):
    """Get a specific policy by ID for the specified persona."""
    import json
    from pathlib import Path
    
    # Mapping of personas to their policy files
    PERSONA_POLICY_FILES = {
        "underwriting": "data/life-health-underwriting-policies.json",
        "life_health_claims": "data/life-health-claims-policies.json",
        "automotive_claims": "data/automotive-claims-policies.json",
        "property_casualty_claims": "data/property-casualty-claims-policies.json",
    }
    
    try:
        # Get the policy file for this persona
        policy_file = PERSONA_POLICY_FILES.get(persona.lower())
        if not policy_file:
            # Fall back to underwriting
            policy_file = PERSONA_POLICY_FILES["underwriting"]
        
        policy_path = Path(policy_file)
        if not policy_path.exists():
            raise HTTPException(status_code=404, detail=f"Policy file not found for persona: {persona}")
        
        with open(policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        policies = data.get("policies", [])
        
        # Find the policy by ID
        for policy in policies:
            if policy.get("id") == policy_id:
                return policy
        
        raise HTTPException(status_code=404, detail=f"Policy not found: {policy_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get policy %s: %s", policy_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/category/{category}")
async def get_policies_by_category(category: str):
    """Get all policies in a specific category."""
    from app.underwriting_policies import get_policies_by_category as get_by_category
    
    try:
        settings = load_settings()
        policies = get_by_category(settings.app.prompts_root, category)
        
        return {
            "category": category,
            "policies": policies,
            "total": len(policies),
        }
    except Exception as e:
        logger.error("Failed to get policies for category %s: %s", category, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Background RAG Indexing Helpers
# =============================================================================

async def _background_reindex_policy(settings, policy_id: str):
    """Background task to reindex a policy after create/update."""
    try:
        from app.rag.indexer import PolicyIndexer
        
        logger.info("Background reindexing policy: %s", policy_id)
        indexer = PolicyIndexer(settings=settings)
        await indexer.reindex_policy(policy_id)
        logger.info("Background reindex complete for policy: %s", policy_id)
    except Exception as e:
        logger.error("Background reindex failed for policy %s: %s", policy_id, e)


async def _background_delete_policy_chunks(settings, policy_id: str):
    """Background task to delete policy chunks after policy deletion."""
    try:
        from app.rag.repository import PolicyChunkRepository
        
        logger.info("Deleting chunks for policy: %s", policy_id)
        repo = PolicyChunkRepository(schema=settings.database.schema or "workbenchiq")
        deleted = await repo.delete_chunks_by_policy(policy_id)
        logger.info("Deleted %d chunks for policy: %s", deleted, policy_id)
    except Exception as e:
        logger.error("Failed to delete chunks for policy %s: %s", policy_id, e)


class PolicyCreateRequest(BaseModel):
    """Request model for creating a policy."""
    id: str
    category: str
    subcategory: str
    name: str
    description: str
    criteria: List[dict] = []
    modifying_factors: List[dict] = []
    references: List[str] = []


class PolicyUpdateRequest(BaseModel):
    """Request model for updating a policy."""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[List[dict]] = None
    modifying_factors: Optional[List[dict]] = None
    references: Optional[List[str]] = None


@app.post("/api/policies")
async def create_policy(request: PolicyCreateRequest):
    """Create a new underwriting policy."""
    from app.underwriting_policies import add_policy
    
    try:
        settings = load_settings()
        policy_data = request.model_dump()
        result = add_policy(settings.app.prompts_root, policy_data)
        
        logger.info("Created policy %s", request.id)
        
        # Trigger background reindex if PostgreSQL is enabled
        if settings.database.backend == "postgresql":
            import asyncio
            asyncio.create_task(_background_reindex_policy(settings, request.id))
        
        return {
            "message": "Policy created successfully",
            "policy": result["policy"]
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Failed to create policy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/policies/{policy_id}")
async def update_policy_endpoint(policy_id: str, request: PolicyUpdateRequest):
    """Update an existing underwriting policy."""
    from app.underwriting_policies import update_policy
    
    try:
        settings = load_settings()
        # Only include non-None values in the update
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        result = update_policy(settings.app.prompts_root, policy_id, update_data)
        
        logger.info("Updated policy %s", policy_id)
        
        # Trigger background reindex if PostgreSQL is enabled
        if settings.database.backend == "postgresql":
            import asyncio
            asyncio.create_task(_background_reindex_policy(settings, policy_id))
        
        return {
            "message": "Policy updated successfully",
            "policy": result["policy"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to update policy %s: %s", policy_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/policies/{policy_id}")
async def delete_policy_endpoint(policy_id: str):
    """Delete an underwriting policy."""
    from app.underwriting_policies import delete_policy
    
    try:
        settings = load_settings()
        result = delete_policy(settings.app.prompts_root, policy_id)
        
        logger.info("Deleted policy %s", policy_id)
        
        # Delete from RAG index if PostgreSQL is enabled
        if settings.database.backend == "postgresql":
            import asyncio
            asyncio.create_task(_background_delete_policy_chunks(settings, policy_id))
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete policy %s: %s", policy_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Chat API Endpoints
# =============================================================================

@app.post("/api/applications/{app_id}/chat")
async def chat_with_application(app_id: str, request: ChatRequest):
    """Chat about an application with policy context."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from app.openai_client import chat_completion
    from app.underwriting_policies import format_all_policies_for_prompt, format_policies_for_persona
    
    try:
        settings = load_settings()
        
        # Determine persona - use from request or default to underwriting
        persona = request.persona or "underwriting"
        
        # Load application data
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
        
        # Build augmented RAG query with claim/application context for better retrieval
        rag_query = request.message
        if app_md.document_markdown:
            # Extract first ~500 chars of document for context augmentation
            doc_context = app_md.document_markdown[:500].replace('\n', ' ').strip()
            rag_query = f"{request.message} Context: {doc_context}"
        
        # Get policy context - use RAG if enabled, otherwise full policies
        rag_result = None
        rag_citations = []
        
        # Get persona-aware fallback context
        fallback_context = format_policies_for_persona(settings.app.prompts_root, persona)
        
        if settings.rag.enabled:
            try:
                from app.rag.service import get_rag_service
                
                # Get persona-aware RAG service
                rag_service = await get_rag_service(settings, persona=persona)
                
                # Use RAG to get relevant policy context based on augmented query
                rag_result = await rag_service.query_with_fallback(
                    user_query=rag_query,
                    fallback_context=fallback_context,
                    top_k=10,  # Get more chunks for chat context
                )
                
                policies_context = rag_service.format_context_for_prompt(rag_result)
                rag_citations = rag_service.get_citations_for_response(rag_result)
                
                logger.info(
                    "Chat [%s]: RAG retrieved %d chunks (%d tokens) in %.0fms%s",
                    persona,
                    rag_result.chunks_retrieved,
                    rag_result.tokens_used,
                    rag_result.total_latency_ms,
                    " [FALLBACK]" if rag_result.used_fallback else ""
                )
                
            except Exception as e:
                logger.warning("Chat [%s]: RAG failed, falling back to full policies: %s", persona, e)
                policies_context = fallback_context
        else:
            # RAG disabled - use full policies for persona
            policies_context = fallback_context
            logger.info("Chat [%s]: Loaded %d chars of policy context (RAG disabled)", persona, len(policies_context))
        
        # Build context from application data
        app_context_parts = []
        
        # Add document markdown if available
        if app_md.document_markdown:
            # Truncate to avoid token limits
            doc_preview = app_md.document_markdown[:8000]
            if len(app_md.document_markdown) > 8000:
                doc_preview += "\n\n[Document truncated for chat context...]"
            app_context_parts.append(f"## Application Documents\n\n{doc_preview}")
        
        # Add LLM analysis outputs
        if app_md.llm_outputs:
            analysis_summary = []
            for section, subsections in app_md.llm_outputs.items():
                if not subsections:
                    continue
                for subsection, output in subsections.items():
                    if output and output.get("parsed"):
                        parsed = output["parsed"]
                        if isinstance(parsed, dict):
                            # Extract key information
                            risk = parsed.get("risk_assessment", "")
                            summary = parsed.get("summary", parsed.get("family_history_summary", ""))
                            if risk or summary:
                                analysis_summary.append(f"- {section}.{subsection}: {risk or summary}")
            
            if analysis_summary:
                app_context_parts.append("## Analysis Summary\n\n" + "\n".join(analysis_summary))
        
        # Build persona-aware system message
        system_message = get_chat_system_prompt(
            persona=persona,
            policies_context=policies_context,
            app_id=app_id,
            app_context_parts=app_context_parts,
        )

        # Build messages array
        messages = [{"role": "system", "content": system_message}]
        
        # Add chat history
        if request.history:
            for msg in request.history:
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        logger.info("Chat: Sending %d messages to OpenAI", len(messages))
        
        # Use chat-specific deployment if configured, otherwise fall back to main model
        chat_deployment = settings.openai.chat_deployment_name or settings.openai.deployment_name
        chat_model = settings.openai.chat_model_name or settings.openai.model_name
        chat_api_version = settings.openai.chat_api_version or settings.openai.api_version
        logger.info("Chat: Using deployment=%s, model=%s, api_version=%s", chat_deployment, chat_model, chat_api_version)
        
        # Call OpenAI in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: chat_completion(
                    settings.openai, 
                    messages, 
                    max_tokens=2000,
                    deployment_override=chat_deployment,
                    model_override=chat_model,
                    api_version_override=chat_api_version
                )
            )
        
        logger.info("Chat: Received response from OpenAI")
        
        # Build response with optional RAG metadata
        response_data = {
            "response": result["content"],
            "usage": result.get("usage", {}),
        }
        
        # Add RAG metadata if available
        if rag_result and not rag_result.used_fallback:
            response_data["rag"] = {
                "enabled": True,
                "chunks_retrieved": rag_result.chunks_retrieved,
                "tokens_used": rag_result.tokens_used,
                "latency_ms": round(rag_result.total_latency_ms),
                "citations": rag_citations,
                "inferred_categories": rag_result.inferred.categories if rag_result.inferred else [],
            }
        elif rag_result and rag_result.used_fallback:
            response_data["rag"] = {
                "enabled": True,
                "fallback": True,
                "fallback_reason": rag_result.fallback_reason,
            }
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat failed for application %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Conversation History API Endpoints
# =============================================================================

def get_conversations_dir(storage_root: str) -> Path:
    """Get the conversations directory path."""
    return Path(storage_root) / "conversations"


def get_app_conversations_dir(storage_root: str, app_id: str) -> Path:
    """Get the conversations directory for a specific application."""
    return get_conversations_dir(storage_root) / app_id


def load_conversation(storage_root: str, app_id: str, conversation_id: str) -> Optional[dict]:
    """Load a conversation from disk."""
    conv_file = get_app_conversations_dir(storage_root, app_id) / f"{conversation_id}.json"
    if conv_file.exists():
        try:
            return json.loads(conv_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to load conversation %s: %s", conversation_id, e)
    return None


def save_conversation(storage_root: str, app_id: str, conversation: dict) -> None:
    """Save a conversation to disk."""
    conv_dir = get_app_conversations_dir(storage_root, app_id)
    conv_dir.mkdir(parents=True, exist_ok=True)
    conv_file = conv_dir / f"{conversation['id']}.json"
    conv_file.write_text(json.dumps(conversation, indent=2), encoding="utf-8")


def list_conversations(storage_root: str, app_id: str) -> List[dict]:
    """List all conversations for an application."""
    conv_dir = get_app_conversations_dir(storage_root, app_id)
    if not conv_dir.exists():
        return []
    
    conversations = []
    for conv_file in conv_dir.glob("*.json"):
        try:
            conv = json.loads(conv_file.read_text(encoding="utf-8"))
            # Create summary
            messages = conv.get("messages", [])
            preview = None
            if messages:
                # Get first user message as preview
                for msg in messages:
                    if msg.get("role") == "user":
                        preview = msg.get("content", "")[:100]
                        if len(msg.get("content", "")) > 100:
                            preview += "..."
                        break
            
            conversations.append({
                "id": conv["id"],
                "application_id": conv.get("application_id", app_id),
                "title": conv.get("title", "Untitled Conversation"),
                "created_at": conv.get("created_at", ""),
                "updated_at": conv.get("updated_at", ""),
                "message_count": len(messages),
                "preview": preview,
            })
        except Exception as e:
            logger.error("Failed to read conversation file %s: %s", conv_file, e)
    
    # Sort by updated_at descending
    conversations.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return conversations


def generate_conversation_title(first_message: str) -> str:
    """Generate a title from the first user message."""
    # Take first 50 chars and clean up
    title = first_message[:50].strip()
    if len(first_message) > 50:
        title += "..."
    return title or "New Conversation"


@app.get("/api/applications/{app_id}/conversations")
async def get_application_conversations(app_id: str):
    """List all conversations for an application."""
    try:
        settings = load_settings()
        conversations = list_conversations(settings.app.storage_root, app_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error("Failed to list conversations for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations")
async def get_all_conversations(limit: int = 50):
    """List conversations across all applications."""
    try:
        settings = load_settings()
        storage_root = Path(settings.app.storage_root)
        
        all_conversations = []
        
        # Iterate through all application directories
        if storage_root.exists():
            # Check for conversations in data/conversations/ (legacy)
            conversations_dir = storage_root / "conversations"
            if conversations_dir.exists():
                for app_dir in conversations_dir.iterdir():
                    if app_dir.is_dir():
                        app_id = app_dir.name
                        convs = list_conversations(settings.app.storage_root, app_id)
                        all_conversations.extend(convs)
            
            # Check for conversations in data/applications/*/conversations/
            applications_dir = storage_root / "applications"
            if applications_dir.exists():
                for app_dir in applications_dir.iterdir():
                    if app_dir.is_dir():
                        app_id = app_dir.name
                        app_conv_dir = app_dir / "conversations"
                        if app_conv_dir.exists():
                            for conv_file in app_conv_dir.glob("*.json"):
                                try:
                                    conv = json.loads(conv_file.read_text(encoding="utf-8"))
                                    messages = conv.get("messages", [])
                                    preview = None
                                    if messages:
                                        for msg in messages:
                                            if msg.get("role") == "user":
                                                preview = msg.get("content", "")[:100]
                                                if len(msg.get("content", "")) > 100:
                                                    preview += "..."
                                                break
                                    
                                    all_conversations.append({
                                        "id": conv["id"],
                                        "application_id": app_id,
                                        "title": conv.get("title", "Untitled Conversation"),
                                        "created_at": conv.get("created_at", ""),
                                        "updated_at": conv.get("updated_at", ""),
                                        "message_count": len(messages),
                                        "preview": preview,
                                    })
                                except Exception as e:
                                    logger.error("Failed to read conversation file %s: %s", conv_file, e)
        
        # Sort by updated_at descending (most recent first)
        all_conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Apply limit
        all_conversations = all_conversations[:limit]
        
        return {"conversations": all_conversations}
    except Exception as e:
        logger.error("Failed to list all conversations: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{app_id}/conversations/{conversation_id}")
async def get_conversation(app_id: str, conversation_id: str):
    """Get a specific conversation with all messages."""
    try:
        settings = load_settings()
        conversation = load_conversation(settings.app.storage_root, app_id, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation %s: %s", conversation_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/applications/{app_id}/conversations/{conversation_id}")
async def delete_conversation(app_id: str, conversation_id: str):
    """Delete a conversation."""
    try:
        settings = load_settings()
        conv_file = get_app_conversations_dir(settings.app.storage_root, app_id) / f"{conversation_id}.json"
        if not conv_file.exists():
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_file.unlink()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete conversation %s: %s", conversation_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/conversations")
async def create_or_continue_conversation(app_id: str, request: ChatRequest):
    """Create a new conversation or continue an existing one, and get AI response."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from app.openai_client import chat_completion
    from app.underwriting_policies import format_all_policies_for_prompt, format_policies_for_persona
    from datetime import datetime
    import uuid
    
    try:
        settings = load_settings()
        now = datetime.utcnow().isoformat() + "Z"
        
        # Determine persona - use from request or default to underwriting
        persona = request.persona or "underwriting"
        
        # Load or create conversation
        if request.conversation_id:
            conversation = load_conversation(settings.app.storage_root, app_id, request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = {
                "id": str(uuid.uuid4())[:8],
                "application_id": app_id,
                "title": generate_conversation_title(request.message),
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "persona": persona,  # Store persona with conversation
            }
        
        # Add user message
        user_message = {
            "role": "user",
            "content": request.message,
            "timestamp": now,
        }
        conversation["messages"].append(user_message)
        conversation["updated_at"] = now
        
        # Load application data
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
        
        # Build augmented RAG query with claim/application context for better retrieval
        rag_query = request.message
        if app_md.document_markdown:
            # Extract first ~500 chars of document for context augmentation
            doc_context = app_md.document_markdown[:500].replace('\n', ' ').strip()
            rag_query = f"{request.message} Context: {doc_context}"
        
        # Get policy context - use RAG if enabled, otherwise full policies
        rag_result = None
        rag_citations = []
        
        # Get persona-aware fallback context
        fallback_context = format_policies_for_persona(settings.app.prompts_root, persona)
        
        if settings.rag.enabled:
            try:
                from app.rag.service import get_rag_service
                
                # Get persona-aware RAG service
                rag_service = await get_rag_service(settings, persona=persona)
                
                # Use RAG to get relevant policy context based on augmented query
                rag_result = await rag_service.query_with_fallback(
                    user_query=rag_query,
                    fallback_context=fallback_context,
                    top_k=10,
                )
                
                policies_context = rag_service.format_context_for_prompt(rag_result)
                rag_citations = rag_service.get_citations_for_response(rag_result)
                
                logger.info(
                    "Conversation [%s]: RAG retrieved %d chunks (%d tokens) in %.0fms%s",
                    persona,
                    rag_result.chunks_retrieved,
                    rag_result.tokens_used,
                    rag_result.total_latency_ms,
                    " [FALLBACK]" if rag_result.used_fallback else ""
                )
                
            except Exception as e:
                logger.warning("Conversation [%s]: RAG failed, falling back to full policies: %s", persona, e)
                policies_context = fallback_context
        else:
            # RAG disabled - use full policies for persona
            policies_context = fallback_context
            logger.info("Conversation [%s]: Loaded %d chars of policy context (RAG disabled)", persona, len(policies_context))
        
        # Build context from application data
        app_context_parts = []
        
        if app_md.document_markdown:
            doc_preview = app_md.document_markdown[:8000]
            if len(app_md.document_markdown) > 8000:
                doc_preview += "\n\n[Document truncated for chat context...]"
            app_context_parts.append(f"## Application Documents\n\n{doc_preview}")
        
        if app_md.llm_outputs:
            analysis_summary = []
            for section, subsections in app_md.llm_outputs.items():
                if not subsections:
                    continue
                for subsection, output in subsections.items():
                    if output and output.get("parsed"):
                        parsed = output["parsed"]
                        if isinstance(parsed, dict):
                            risk = parsed.get("risk_assessment", "")
                            summary = parsed.get("summary", parsed.get("family_history_summary", ""))
                            if risk or summary:
                                analysis_summary.append(f"- {section}.{subsection}: {risk or summary}")
            
            if analysis_summary:
                app_context_parts.append("## Analysis Summary\n\n" + "\n".join(analysis_summary))
        
        # Build persona-aware system message
        system_message = get_chat_system_prompt(
            persona=persona,
            policies_context=policies_context,
            app_id=app_id,
            app_context_parts=app_context_parts,
        )

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_message}]
        for msg in conversation["messages"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        logger.info("Conversation: Sending %d messages to OpenAI", len(messages))
        
        # Use chat-specific deployment
        chat_deployment = settings.openai.chat_deployment_name or settings.openai.deployment_name
        chat_model = settings.openai.chat_model_name or settings.openai.model_name
        chat_api_version = settings.openai.chat_api_version or settings.openai.api_version
        
        # Call OpenAI
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: chat_completion(
                    settings.openai, 
                    messages, 
                    max_tokens=2000,
                    deployment_override=chat_deployment,
                    model_override=chat_model,
                    api_version_override=chat_api_version
                )
            )
        
        # Add assistant response
        assistant_message = {
            "role": "assistant",
            "content": result["content"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        conversation["messages"].append(assistant_message)
        conversation["updated_at"] = assistant_message["timestamp"]
        
        # Save conversation
        save_conversation(settings.app.storage_root, app_id, conversation)
        
        logger.info("Conversation: Saved conversation %s with %d messages", 
                   conversation["id"], len(conversation["messages"]))
        
        # Build response with optional RAG metadata
        response_data = {
            "conversation_id": conversation["id"],
            "response": result["content"],
            "usage": result.get("usage", {}),
            "title": conversation["title"],
        }
        
        # Add RAG metadata if available
        if rag_result and not rag_result.used_fallback:
            response_data["rag"] = {
                "enabled": True,
                "chunks_retrieved": rag_result.chunks_retrieved,
                "tokens_used": rag_result.tokens_used,
                "latency_ms": round(rag_result.total_latency_ms),
                "citations": rag_citations,
                "inferred_categories": rag_result.inferred.categories if rag_result.inferred else [],
            }
        elif rag_result and rag_result.used_fallback:
            response_data["rag"] = {
                "enabled": True,
                "fallback": True,
                "fallback_reason": rag_result.fallback_reason,
            }
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Conversation failed for application %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Health Check API Endpoints
# =============================================================================

@app.get("/api/health/database")
async def health_check_database():
    """Database health check endpoint."""
    from app.database.pool import get_pool
    settings = load_settings()
    if settings.database.backend != "postgresql":
        return {"status": "skipped", "message": "Not using PostgreSQL backend."}
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version();")
            return {"status": "ok", "version": version}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# RAG Indexing API Endpoints
# =============================================================================

class ReindexRequest(BaseModel):
    force: bool = True  # Whether to delete existing chunks first


class ReindexResponse(BaseModel):
    status: str
    policies_indexed: Optional[int] = None
    chunks_stored: Optional[int] = None
    total_time_seconds: Optional[float] = None
    error: Optional[str] = None


@app.post("/api/admin/policies/reindex", response_model=ReindexResponse)
async def reindex_all_policies(
    request: ReindexRequest = ReindexRequest(),
    persona: str = Query(default="underwriting", description="Persona to reindex policies for"),
):
    """
    Reindex all policies for a specific persona's RAG search.
    
    Supported personas:
    - underwriting: Life & health underwriting policies
    - life_health_claims: Health claims processing policies
    - automotive_claims: Automotive claims policies
    - property_casualty_claims: P&C claims policies
    
    This will:
    1. Load all policies from the persona's JSON file
    2. Chunk them into searchable segments
    3. Generate embeddings via Azure OpenAI
    4. Store in PostgreSQL with pgvector
    
    Use force=True (default) to delete existing chunks before reindexing.
    """
    settings = load_settings()
    
    # Check if RAG is enabled
    if settings.database.backend != "postgresql":
        return ReindexResponse(
            status="skipped",
            error="PostgreSQL backend not configured. Set DATABASE_BACKEND=postgresql."
        )
    
    try:
        from app.rag.persona_indexer import get_indexer_for_persona, persona_supports_rag
        
        if not persona_supports_rag(persona):
            return ReindexResponse(
                status="error",
                error=f"Persona '{persona}' does not support RAG indexing."
            )
        
        indexer = await get_indexer_for_persona(persona, settings)
        metrics = await indexer.index_policies(force_reindex=request.force)
        
        return ReindexResponse(
            status=metrics.get("status", "unknown"),
            policies_indexed=metrics.get("policies_indexed"),
            chunks_stored=metrics.get("chunks_stored"),
            total_time_seconds=metrics.get("total_time_seconds"),
        )
    except Exception as e:
        logger.error("Failed to reindex policies for %s: %s", persona, e, exc_info=True)
        return ReindexResponse(status="error", error=str(e))


@app.post("/api/admin/policies/{policy_id}/reindex", response_model=ReindexResponse)
async def reindex_single_policy(policy_id: str):
    """
    Reindex a single policy by ID.
    
    Useful after editing a policy in the UI.
    """
    settings = load_settings()
    
    if settings.database.backend != "postgresql":
        return ReindexResponse(
            status="skipped",
            error="PostgreSQL backend not configured."
        )
    
    try:
        from app.rag.indexer import PolicyIndexer
        
        indexer = PolicyIndexer(settings=settings)
        metrics = await indexer.reindex_policy(policy_id)
        
        if metrics.get("status") == "skipped":
            return ReindexResponse(
                status="not_found",
                error=f"Policy '{policy_id}' not found."
            )
        
        return ReindexResponse(
            status=metrics.get("status", "unknown"),
            policies_indexed=metrics.get("policies_indexed"),
            chunks_stored=metrics.get("chunks_stored"),
            total_time_seconds=metrics.get("total_time_seconds"),
        )
    except Exception as e:
        logger.error("Failed to reindex policy %s: %s", policy_id, e, exc_info=True)
        return ReindexResponse(status="error", error=str(e))


@app.get("/api/admin/policies/index-stats")
async def get_index_stats(
    persona: str = Query(default="underwriting", description="Persona to get index stats for"),
):
    """
    Get statistics about the current policy index for a persona.
    
    Supported personas:
    - underwriting: Life & health underwriting policies
    - life_health_claims: Health claims processing policies
    - automotive_claims: Automotive claims policies
    - property_casualty_claims: P&C claims policies
    """
    settings = load_settings()
    
    if settings.database.backend != "postgresql":
        return {"status": "skipped", "error": "PostgreSQL backend not configured."}
    
    try:
        from app.rag.persona_indexer import get_index_stats_for_persona, persona_supports_rag
        
        if not persona_supports_rag(persona):
            return {"status": "error", "error": f"Persona '{persona}' does not support RAG indexing."}
        
        stats = await get_index_stats_for_persona(persona, settings)
        return stats
    except Exception as e:
        logger.error("Failed to get index stats for %s: %s", persona, e, exc_info=True)
        return {"status": "error", "error": str(e)}


# ============================================================================
# Claims Policy Admin Endpoints (Deprecated - use /api/admin/policies/* with persona param)
# ============================================================================

@app.post("/api/admin/claims-policies/reindex", response_model=ReindexResponse)
async def reindex_all_claims_policies(request: ReindexRequest = ReindexRequest()):
    """
    [DEPRECATED] Reindex automotive claims policies.
    
    Use POST /api/admin/policies/reindex?persona=automotive_claims instead.
    This endpoint is maintained for backwards compatibility.
    """
    # Redirect to unified endpoint
    return await reindex_all_policies(request, persona="automotive_claims")


@app.get("/api/admin/claims-policies/index-stats")
async def get_claims_index_stats():
    """
    [DEPRECATED] Get automotive claims policy index stats.
    
    Use GET /api/admin/policies/index-stats?persona=automotive_claims instead.
    This endpoint is maintained for backwards compatibility.
    """
    # Redirect to unified endpoint
    return await get_index_stats(persona="automotive_claims")


# Entry point for running with uvicorn directly
def main():
    """Entry point for the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
