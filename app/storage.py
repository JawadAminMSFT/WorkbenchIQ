
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StoredFile:
    filename: str
    path: str
    url: Optional[str] = None


@dataclass
class ExtractedFieldConfidence:
    """Represents an extracted field with confidence score and source grounding."""
    field_name: str
    value: Any
    confidence: float
    page_number: Optional[int] = None
    bounding_box: Optional[List[float]] = None
    source_text: Optional[str] = None


@dataclass
class ConfidenceSummary:
    """Summary of confidence scores across all extracted fields."""
    total_fields: int = 0
    average_confidence: float = 0.0
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    high_confidence_fields: List[Dict[str, Any]] = field(default_factory=list)
    medium_confidence_fields: List[Dict[str, Any]] = field(default_factory=list)
    low_confidence_fields: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ApplicationMetadata:
    id: str
    created_at: str
    external_reference: Optional[str]
    status: str
    files: List[StoredFile]
    persona: Optional[str] = None  # Persona this application belongs to
    document_markdown: Optional[str] = None
    markdown_pages: Optional[List[Dict[str, Any]]] = None
    cu_raw_result_path: Optional[str] = None
    llm_outputs: Optional[Dict[str, Any]] = None
    # New fields for confidence scoring
    extracted_fields: Optional[Dict[str, Any]] = None  # Raw extracted fields with confidence
    confidence_summary: Optional[Dict[str, Any]] = None  # Aggregated confidence statistics
    analyzer_id_used: Optional[str] = None  # Which analyzer was used for extraction
    # Risk analysis results (separate from main LLM outputs)
    risk_analysis: Optional[Dict[str, Any]] = None  # Policy-based risk assessment
    # Background processing status tracking
    processing_status: Optional[str] = None  # idle, extracting, analyzing, error
    processing_error: Optional[str] = None  # Error message if processing failed


# =============================================================================
# Storage Provider Integration
# =============================================================================

def _get_provider():
    """Get the storage provider if initialized, or None for legacy fallback."""
    try:
        from app.storage_providers import get_storage_provider
        return get_storage_provider()
    except RuntimeError:
        # Provider not initialized - use legacy local storage
        return None


def load_file_content(stored_file: StoredFile) -> Optional[bytes]:
    """Load file content from storage.
    
    This function handles both local filesystem and Azure Blob Storage.
    It uses the storage provider if initialized, otherwise falls back to
    reading directly from the filesystem path.
    
    Args:
        stored_file: StoredFile object containing path information.
        
    Returns:
        File content as bytes, or None if file not found.
    """
    provider = _get_provider()
    
    if provider:
        # Use storage provider to load file
        content = provider.load_file_by_path(stored_file.path)
        if content is None:
            logger.warning("File not found via provider: %s", stored_file.path)
        return content
    else:
        # Legacy fallback: read directly from filesystem
        path = Path(stored_file.path)
        if not path.exists():
            logger.warning("File not found on filesystem: %s", path)
            return None
        return path.read_bytes()


# =============================================================================
# Legacy Local Storage Helpers
# =============================================================================

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_storage_root(root: str) -> Path:
    p = Path(root)
    _ensure_dir(p)
    return p


def get_application_dir(root: str, app_id: str) -> Path:
    base = get_storage_root(root) / "applications" / app_id
    _ensure_dir(base)
    return base


def save_uploaded_files(
    root: str,
    app_id: str,
    uploaded_files: List[Any],
    public_base_url: Optional[str] = None,
) -> List[StoredFile]:
    """Save uploaded files and return metadata.
    
    Delegates to storage provider if initialized, otherwise uses local filesystem.
    Accepts dicts with 'name' and 'content' keys (from FastAPI after async read).
    """
    provider = _get_provider()
    stored: List[StoredFile] = []

    for f in uploaded_files:
        # Handle dict format from FastAPI (pre-read content)
        if isinstance(f, dict):
            filename = f.get("name", f"upload-{len(stored)}.bin")
            data = f.get("content", b"")
        else:
            # Legacy support for objects with .name and .read()
            filename = getattr(f, "name", f"upload-{len(stored)}.bin")
            data = f.read() if hasattr(f, "read") else f
        
        if provider:
            # Use storage provider
            path = provider.save_file(app_id, filename, data)
            url = provider.get_file_url(app_id, filename)
        else:
            # Legacy local storage
            app_dir = get_application_dir(root, app_id)
            files_dir = app_dir / "files"
            _ensure_dir(files_dir)
            target_path = files_dir / filename
            with open(target_path, "wb") as out:
                out.write(data)
            path = str(target_path)
            url = None
            if public_base_url:
                url = f"{public_base_url.rstrip('/')}/applications/{app_id}/files/{filename}"
        
        stored.append(StoredFile(filename=filename, path=path, url=url))

    return stored


def save_cu_raw_result(root: str, app_id: str, payload: Dict[str, Any]) -> str:
    """Save Content Understanding raw result JSON."""
    provider = _get_provider()
    
    if provider:
        return provider.save_cu_result(app_id, payload)
    else:
        # Legacy local storage
        app_dir = get_application_dir(root, app_id)
        cu_path = app_dir / "content_understanding.json"
        with open(cu_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return str(cu_path)


def _metadata_to_dict(metadata: ApplicationMetadata) -> Dict[str, Any]:
    """Convert ApplicationMetadata to a serializable dictionary."""
    serializable = asdict(metadata)
    serializable["files"] = [asdict(f) for f in metadata.files]
    return serializable


def _dict_to_metadata(data: Dict[str, Any]) -> ApplicationMetadata:
    """Convert a dictionary to ApplicationMetadata."""
    files = [StoredFile(**fd) for fd in data.get("files", [])]
    return ApplicationMetadata(
        id=data["id"],
        created_at=data.get("created_at"),
        external_reference=data.get("external_reference"),
        status=data.get("status", "unknown"),
        files=files,
        persona=data.get("persona"),
        document_markdown=data.get("document_markdown"),
        markdown_pages=data.get("markdown_pages"),
        cu_raw_result_path=data.get("cu_raw_result_path"),
        llm_outputs=data.get("llm_outputs"),
        extracted_fields=data.get("extracted_fields"),
        confidence_summary=data.get("confidence_summary"),
        analyzer_id_used=data.get("analyzer_id_used"),
        risk_analysis=data.get("risk_analysis"),
        processing_status=data.get("processing_status"),
        processing_error=data.get("processing_error"),
    )


def save_application_metadata(root: str, metadata: ApplicationMetadata) -> None:
    """Save application metadata."""
    provider = _get_provider()
    serializable = _metadata_to_dict(metadata)
    
    if provider:
        provider.save_metadata(metadata.id, serializable)
    else:
        # Legacy local storage
        app_dir = get_application_dir(root, metadata.id)
        meta_path = app_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)


def load_application(root: str, app_id: str) -> Optional[ApplicationMetadata]:
    """Load application metadata."""
    provider = _get_provider()
    
    if provider:
        data = provider.load_metadata(app_id)
        if data is None:
            return None
        return _dict_to_metadata(data)
    else:
        # Legacy local storage
        app_dir = get_application_dir(root, app_id)
        meta_path = app_dir / "metadata.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _dict_to_metadata(data)


def list_applications(root: str, persona: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return lightweight list of available applications, optionally filtered by persona."""
    from app.personas import normalize_persona_id
    
    provider = _get_provider()
    
    # Normalize the filter persona (handles legacy 'claims' -> 'life_health_claims')
    if persona is not None:
        persona = normalize_persona_id(persona)

    apps: List[Dict[str, Any]] = []
    
    if provider:
        # Use storage provider
        app_ids = provider.list_applications()
        for app_id in app_ids:
            data = provider.load_metadata(app_id)
            if data is None:
                continue
            
            # Filter by persona if specified
            app_persona = data.get("persona") or "underwriting"
            app_persona = normalize_persona_id(app_persona)
            
            if persona is not None and app_persona != persona:
                continue
            
            apps.append(
                {
                    "id": data.get("id"),
                    "created_at": data.get("created_at"),
                    "external_reference": data.get("external_reference"),
                    "status": data.get("status", "unknown"),
                    "persona": app_persona,
                    "processing_status": data.get("processing_status"),
                    "summary_title": data.get("llm_outputs", {})
                    .get("application_summary", {})
                    .get("customer_profile", {})
                    .get("summary", "")
                    or "",
                }
            )
    else:
        # Legacy local storage
        base = get_storage_root(root) / "applications"
        if not base.exists():
            return []

        for app_dir in sorted(base.iterdir()):
            if not app_dir.is_dir():
                continue
            meta_path = app_dir / "metadata.json"
            if not meta_path.exists():
                continue
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Filter by persona if specified
            # Legacy apps without persona are treated as "underwriting"
            app_persona = data.get("persona") or "underwriting"
            # Normalize app persona as well (handles legacy 'claims' in stored data)
            app_persona = normalize_persona_id(app_persona)
            
            if persona is not None and app_persona != persona:
                continue
                
            apps.append(
                {
                    "id": data.get("id"),
                    "created_at": data.get("created_at"),
                    "external_reference": data.get("external_reference"),
                    "status": data.get("status", "unknown"),
                    "persona": app_persona,
                    "processing_status": data.get("processing_status"),
                    "summary_title": data.get("llm_outputs", {})
                    .get("application_summary", {})
                    .get("customer_profile", {})
                    .get("summary", "")
                    or "",
                }
            )
    
    # Sort by created_at descending
    apps.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    return apps


def new_metadata(
    root: str,
    app_id: str,
    files: List[StoredFile],
    external_reference: Optional[str] = None,
    persona: Optional[str] = None,
) -> ApplicationMetadata:
    created_at = datetime.utcnow().isoformat() + "Z"
    md = ApplicationMetadata(
        id=app_id,
        created_at=created_at,
        external_reference=external_reference,
        status="pending",
        files=files,
        persona=persona,
        document_markdown=None,
        markdown_pages=None,
        cu_raw_result_path=None,
        llm_outputs={},
    )
    save_application_metadata(root, md)
    return md
