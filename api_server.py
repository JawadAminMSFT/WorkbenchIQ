"""
FastAPI backend server for the Underwriting Assistant.
This provides REST API endpoints for the Next.js frontend.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import load_settings, validate_settings
from app.storage import (
    list_applications,
    load_application,
    new_metadata,
    save_uploaded_files,
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize storage provider on startup
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


# Pydantic models for API responses
class ApplicationListItem(BaseModel):
    id: str
    created_at: Optional[str]
    external_reference: Optional[str]
    status: str
    persona: Optional[str] = None
    summary_title: Optional[str] = None


class AnalyzeRequest(BaseModel):
    sections: Optional[List[str]] = None


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
    }


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
async def extract_content(app_id: str):
    """Run Content Understanding extraction on an application."""
    try:
        settings = load_settings()
        app_md = load_application(settings.app.storage_root, app_id)
        if not app_md:
            raise HTTPException(status_code=404, detail="Application not found")

        # Run content understanding
        app_md = run_content_understanding_for_files(settings, app_md)
        
        logger.info("Extraction completed for application %s", app_id)
        return application_to_dict(app_md)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Extraction failed for %s: %s", app_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{app_id}/analyze")
async def analyze_application(app_id: str, request: AnalyzeRequest = None):
    """Run underwriting prompts analysis on an application."""
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

        # Run underwriting prompts
        app_md = run_underwriting_prompts(
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
        prompts = load_prompts(settings.app.storage_root, persona)
        return {"prompts": prompts, "persona": persona}
    except Exception as e:
        logger.error("Failed to load prompts: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompts/{section}/{subsection}")
async def get_prompt(section: str, subsection: str, persona: str = "underwriting"):
    """Get a specific prompt by section and subsection."""
    try:
        settings = load_settings()
        prompts = load_prompts(settings.app.storage_root, persona)
        
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
        prompts = load_prompts(settings.app.storage_root, persona)
        
        if section not in prompts:
            prompts[section] = {}
        
        prompts[section][subsection] = request.text
        save_prompts(settings.app.storage_root, prompts, persona)
        
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
        prompts = load_prompts(settings.app.storage_root, persona)
        
        if section in prompts and subsection in prompts[section]:
            del prompts[section][subsection]
            # Remove section if empty
            if not prompts[section]:
                del prompts[section]
            save_prompts(settings.app.storage_root, prompts, persona)
            
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
        prompts = load_prompts(settings.app.storage_root, persona)
        
        if section not in prompts:
            prompts[section] = {}
        
        if subsection in prompts[section]:
            raise HTTPException(
                status_code=409, 
                detail=f"Prompt '{section}/{subsection}' already exists. Use PUT to update."
            )
        
        prompts[section][subsection] = request.text
        save_prompts(settings.app.storage_root, prompts, persona)
        
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
        
        # Get the analyzer_id from persona config if not explicitly provided
        if request and request.analyzer_id:
            analyzer_id = request.analyzer_id
        else:
            try:
                persona_config = get_persona_config(persona_id)
                analyzer_id = persona_config.custom_analyzer_id
            except ValueError:
                # Fallback to default if persona not found
                analyzer_id = settings.content_understanding.custom_analyzer_id
        
        description = request.description if request and request.description else f"Custom {persona_id} analyzer for document extraction with confidence scores"
        
        result = create_or_update_custom_analyzer(
            settings.content_understanding,
            analyzer_id=analyzer_id,
            persona_id=persona_id,
            description=description,
        )
        
        logger.info("Created/updated custom analyzer: %s", analyzer_id)
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
        
        # Check each persona's custom analyzer
        for persona in personas:
            if not persona.get("enabled", True):
                continue  # Skip disabled personas
                
            persona_id = persona["id"]
            try:
                persona_config = get_persona_config(persona_id)
                custom_id = persona_config.custom_analyzer_id
                
                # Try to check if custom analyzer exists
                try:
                    custom_analyzer = get_analyzer(settings.content_understanding, custom_id)
                    if custom_analyzer:
                        analyzers.append({
                            "id": custom_id,
                            "type": "custom",
                            "description": custom_analyzer.get("description", f"Custom {persona['name']} analyzer"),
                            "exists": True,
                            "persona": persona_id,
                            "persona_name": persona["name"],
                        })
                    else:
                        analyzers.append({
                            "id": custom_id,
                            "type": "custom",
                            "description": f"Custom {persona['name']} analyzer (not created yet)",
                            "exists": False,
                            "persona": persona_id,
                            "persona_name": persona["name"],
                        })
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as timeout_err:
                    logger.warning("Timeout checking custom analyzer %s for persona %s: %s", custom_id, persona_id, timeout_err)
                    analyzers.append({
                        "id": custom_id,
                        "type": "custom",
                        "description": f"Custom {persona['name']} analyzer (status unknown - timeout)",
                        "exists": None,
                        "persona": persona_id,
                        "persona_name": persona["name"],
                        "error": f"Request timeout ({timeout_err})",
                    })
                except requests.exceptions.ConnectionError as conn_err:
                    logger.warning("Connection error checking custom analyzer %s for persona %s: %s", custom_id, persona_id, conn_err)
                    analyzers.append({
                        "id": custom_id,
                        "type": "custom",
                        "description": f"Custom {persona['name']} analyzer (status unknown - connection error)",
                        "exists": None,
                        "persona": persona_id,
                        "persona_name": persona["name"],
                        "error": "Cannot connect to Azure Content Understanding service",
                    })
            except Exception as e:
                logger.warning("Error processing persona %s: %s", persona_id, e)
                continue
        
        return {"analyzers": analyzers}
    except Exception as e:
        logger.error("Failed to list analyzers: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Entry point for running with uvicorn directly
def main():
    """Entry point for the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
