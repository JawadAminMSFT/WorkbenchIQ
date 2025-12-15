
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import ContentUnderstandingSettings, UNDERWRITING_FIELD_SCHEMA
from .utils import setup_logging

try:
    from azure.identity import DefaultAzureCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False

logger = setup_logging()

# Polling timeout in seconds for long-running operations
POLL_TIMEOUT_SECONDS = 180

# Cache for Azure AD credential to avoid recreating on every request
_credential_cache: Optional[Any] = None


class ContentUnderstandingError(Exception):
    pass


@dataclass
class FieldConfidence:
    """Represents an extracted field with confidence score and source grounding."""
    field_name: str
    value: Any
    confidence: float
    page_number: Optional[int] = None
    bounding_box: Optional[List[float]] = None
    source_text: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of document extraction with confidence scores."""
    fields: Dict[str, FieldConfidence]
    raw_result: Dict[str, Any]
    analyzer_id: str
    document_markdown: str


def _get_headers(
    subscription_key: Optional[str] = None,
    token: Optional[str] = None,
    x_ms_useragent: str = "underwriting-assistant"
) -> Dict[str, str]:
    """Returns the headers for HTTP requests to Content Understanding API.
    
    Args:
        subscription_key: APIM subscription key (for APIM-based endpoints)
        token: Azure AD bearer token (for direct Cognitive Services endpoints)
        x_ms_useragent: User agent string
    
    Returns:
        Dictionary of HTTP headers
    """
    if subscription_key:
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    elif token:
        headers = {"Authorization": f"Bearer {token}"}
    else:
        raise ValueError("Either subscription_key or token must be provided")
    
    headers["x-ms-useragent"] = x_ms_useragent
    return headers


def _raise_for_status_with_detail(response: requests.Response) -> None:
    """
    Raises HTTPError with detailed error information from the response.
    
    Args:
        response: The HTTP response object to check
        
    Raises:
        requests.exceptions.HTTPError: If the response status indicates an error,
            with additional context from the response body
    """
    if response.ok:
        return
    
    try:
        error_detail = ""
        try:
            error_json = response.json()
            if "error" in error_json:
                error_info = error_json["error"]
                error_code = error_info.get("code", "Unknown")
                error_message = error_info.get("message", "No message provided")
                error_detail = f"\n  Error Code: {error_code}\n  Error Message: {error_message}"
                
                if "details" in error_info:
                    error_detail += f"\n  Details: {error_info['details']}"
                if "innererror" in error_info:
                    error_detail += f"\n  Inner Error: {error_info['innererror']}"
            else:
                error_detail = f"\n  Response Body: {json.dumps(error_json, indent=2)}"
        except (ValueError, json.JSONDecodeError):
            if response.text:
                error_detail = f"\n  Response Text: {response.text[:500]}"
    except Exception:
        error_detail = ""
    
    error_msg = f"{response.status_code} {response.reason} for url: {response.url}{error_detail}"
    http_error = requests.exceptions.HTTPError(error_msg, response=response)
    raise http_error


def poll_result(
    response: requests.Response,
    headers: Dict[str, str],
    timeout_seconds: int = POLL_TIMEOUT_SECONDS,
    polling_interval_seconds: int = 2,
) -> Dict[str, Any]:
    """
    Polls the result of an asynchronous operation until it completes or times out.

    Args:
        response: The initial response object containing the operation location
        headers: Headers to use for polling requests
        timeout_seconds: Maximum seconds to wait for operation completion
        polling_interval_seconds: Seconds to wait between polling attempts

    Raises:
        ValueError: If the operation location is not found in response headers
        TimeoutError: If the operation does not complete within timeout
        RuntimeError: If the operation fails

    Returns:
        The JSON response of the completed operation
    """
    operation_location = response.headers.get("operation-location", "")
    if not operation_location:
        raise ValueError("Operation location not found in response headers.")

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_seconds:
            raise TimeoutError(
                f"Operation timed out after {timeout_seconds:.2f} seconds."
            )

        poll_response = requests.get(operation_location, headers=headers)
        _raise_for_status_with_detail(poll_response)
        
        result = poll_response.json()
        status = result.get("status", "").lower()
        
        if status == "succeeded":
            logger.info(
                f"Request result is ready after {elapsed_time:.2f} seconds."
            )
            return result
        elif status == "failed":
            logger.error(f"Request failed. Reason: {result}")
            raise RuntimeError(f"Request failed: {result}")
        else:
            logger.info(
                f"Request {operation_location.split('/')[-1].split('?')[0]} in progress ..."
            )
        
        time.sleep(polling_interval_seconds)


def analyze_document(
    settings: ContentUnderstandingSettings,
    file_path: str,
    file_bytes: Optional[bytes] = None,
    output_markdown: bool = True,
    max_retries: int = 3,
    retry_backoff: float = 1.5,
) -> Dict[str, Any]:
    """Call Azure AI Content Understanding REST API for a single document.

    Uses the Content Analyzers - Analyze Binary operation (GA API 2025-11-01)
    and targets the prebuilt-documentSearch analyzer by default, which is 
    optimized for RAG and markdown extraction.

    Endpoint shape:
        POST {endpoint}/contentunderstanding/analyzers/{analyzerId}:analyzeBinary?api-version=...

    Where analyzerId is usually `prebuilt-documentSearch`, but you can
    override it using AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID.
    
    Authentication:
        - If use_azure_ad=True: Uses DefaultAzureCredential (recommended for direct Cognitive Services)
        - If use_azure_ad=False: Uses subscription key (for APIM-based endpoints)
    
    Args:
        settings: Content Understanding settings
        file_path: Path to the document file (used if file_bytes not provided)
        file_bytes: Raw file content bytes (preferred for cloud storage)
        output_markdown: Whether to include markdown output
        max_retries: Number of retry attempts
        retry_backoff: Backoff multiplier between retries
    """
    if not settings.endpoint:
        raise ContentUnderstandingError(
            "Azure Content Understanding endpoint is not set. "
            "Please set AZURE_CONTENT_UNDERSTANDING_ENDPOINT."
        )
    
    if not settings.use_azure_ad and not settings.api_key:
        raise ContentUnderstandingError(
            "Azure Content Understanding API key is required when not using Azure AD. "
            "Please set AZURE_CONTENT_UNDERSTANDING_API_KEY or set AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD=true."
        )
    
    if settings.use_azure_ad and not AZURE_IDENTITY_AVAILABLE:
        raise ContentUnderstandingError(
            "azure-identity package is required for Azure AD authentication. "
            "Install it with: uv add azure-identity"
        )

    endpoint = settings.endpoint.rstrip("/")
    analyzer_id = settings.analyzer_id

    # Get authentication token or key
    token = None
    if settings.use_azure_ad:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    # Use the correct GA API endpoint path
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
    params = {"api-version": settings.api_version}
    
    # Headers for binary file upload
    headers = _get_headers(subscription_key=settings.api_key, token=token)
    headers["Content-Type"] = "application/octet-stream"

    if output_markdown:
        params["outputFormat"] = "markdown"

    # Use provided bytes or read from file path
    if file_bytes is None:
        file_bytes = Path(file_path).read_bytes()

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            # Send the analyze request
            resp = requests.post(
                url,
                params=params,
                headers=headers,
                data=file_bytes,
                timeout=120,
            )
            _raise_for_status_with_detail(resp)
            
            # Poll for the result
            result = poll_result(resp, headers)
            return result

        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.warning(
                "Content Understanding analyze_document attempt %s failed: %s",
                attempt,
                str(exc),
            )
            if attempt < max_retries:
                time.sleep(retry_backoff**attempt)

    raise ContentUnderstandingError(
        f"Content Understanding analyze_document failed after {max_retries} attempts: {last_err}"
    )


def extract_markdown_from_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise the CU result into a combined markdown + page list.
    
    Follows the GA API 2025-11-01 response structure where results are in:
    payload["result"]["contents"][0]["markdown"]

    Returns:
        {
          "document_markdown": "...",
          "pages": [
            {"page_number": 1, "markdown": "..."},
            ...
          ]
        }
    """
    pages: List[Dict[str, Any]] = []

    # Strategy 1: GA API 2025-11-01 format - result.contents[].markdown
    result = payload.get("result", {})
    contents = result.get("contents", [])
    
    if contents:
        for content in contents:
            # Get markdown from content
            markdown = content.get("markdown", "")
            
            # Check if this is document content with page information
            if content.get("kind") == "document" and markdown:
                # Get page info if available
                pages_data = content.get("pages", [])
                start_page = content.get("startPageNumber", 1)
                end_page = content.get("endPageNumber", start_page)
                
                # If we have page-level data, split accordingly
                if pages_data:
                    for page_info in pages_data:
                        page_num = page_info.get("pageNumber", len(pages) + 1)
                        pages.append({
                            "page_number": page_num,
                            "markdown": markdown,  # Full markdown for now
                            "width": page_info.get("width"),
                            "height": page_info.get("height"),
                        })
                else:
                    # No page breakdown, treat as single document
                    pages.append({
                        "page_number": start_page,
                        "markdown": markdown,
                    })
            elif markdown:
                # Other content types (audioVisual, etc.)
                pages.append({
                    "page_number": 1,
                    "markdown": markdown,
                    "kind": content.get("kind"),
                })

    # Strategy 2: Legacy format - top-level "pages" with markdown content
    if not pages:
        for page in payload.get("pages", []) or []:
            md = page.get("markdown") or page.get("content") or ""
            number = page.get("pageNumber") or page.get("pageIndex") or len(pages) + 1
            if md:
                pages.append({"page_number": number, "markdown": md})

    # Strategy 3: Legacy format - documents[0].content.markdown
    if not pages:
        docs = payload.get("documents") or []
        if docs:
            doc0 = docs[0]
            content = doc0.get("content") or {}
            if isinstance(content, str):
                pages.append({"page_number": 1, "markdown": content})
            elif isinstance(content, dict):
                md = content.get("markdown") or content.get("text") or ""
                if md:
                    pages.append({"page_number": 1, "markdown": md})

    # Fallback: raw payload as JSON string
    if not pages:
        logger.warning("Could not extract markdown from result, using raw JSON")
        pages.append(
            {
                "page_number": 1,
                "markdown": "```json\n" + json.dumps(payload, indent=2) + "\n```",
            }
        )

    document_markdown = "\n\n".join(p["markdown"] for p in pages)

    return {"document_markdown": document_markdown, "pages": pages}


def _get_auth_token_and_headers(settings: ContentUnderstandingSettings) -> tuple[Optional[str], Dict[str, str]]:
    """Get authentication token and headers for API calls."""
    global _credential_cache
    token = None
    if settings.use_azure_ad:
        if not AZURE_IDENTITY_AVAILABLE:
            raise ContentUnderstandingError(
                "azure-identity package is required for Azure AD authentication. "
                "Install it with: uv add azure-identity"
            )
        # Cache the credential to avoid expensive re-initialization
        if _credential_cache is None:
            logger.info("Initializing Azure AD credential (first time only)")
            _credential_cache = DefaultAzureCredential()
        # Get token from cached credential (tokens are cached internally by azure-identity)
        token = _credential_cache.get_token("https://cognitiveservices.azure.com/.default").token
    
    headers = _get_headers(subscription_key=settings.api_key, token=token)
    return token, headers


def get_analyzer(
    settings: ContentUnderstandingSettings,
    analyzer_id: str,
) -> Optional[Dict[str, Any]]:
    """Get an existing analyzer configuration.
    
    Args:
        settings: Content Understanding settings
        analyzer_id: ID of the analyzer to retrieve
    
    Returns:
        Analyzer configuration dict or None if not found
    """
    endpoint = settings.endpoint.rstrip("/")
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": settings.api_version}
    
    _, headers = _get_auth_token_and_headers(settings)
    headers["Content-Type"] = "application/json"
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None
        _raise_for_status_with_detail(resp)
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if "404" in str(e):
            return None
        raise
    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
        logger.warning("Timeout getting analyzer %s: %s", analyzer_id, e)
        raise


def create_or_update_custom_analyzer(
    settings: ContentUnderstandingSettings,
    analyzer_id: Optional[str] = None,
    persona_id: Optional[str] = None,
    field_schema: Optional[Dict[str, Any]] = None,
    description: str = "Custom analyzer for document extraction with confidence scores",
    force_recreate: bool = True,
) -> Dict[str, Any]:
    """Create or update a custom analyzer with field schema for confidence scoring.
    
    Args:
        settings: Content Understanding settings
        analyzer_id: ID for the custom analyzer (defaults to settings.custom_analyzer_id)
        persona_id: Persona ID to determine field schema (e.g., 'underwriting', 'life_health_claims')
        field_schema: Field schema definition (overrides persona_id if provided)
        description: Description of the analyzer
        force_recreate: If True, delete existing analyzer and recreate (default True)
    
    Returns:
        The created/updated analyzer configuration
    """
    if not settings.endpoint:
        raise ContentUnderstandingError(
            "Azure Content Understanding endpoint is not set."
        )
    
    analyzer_id = analyzer_id or settings.custom_analyzer_id
    
    # Determine field schema: explicit > persona-based > default underwriting
    if field_schema is None:
        if persona_id:
            from app.personas import get_field_schema
            field_schema = get_field_schema(persona_id)
        else:
            field_schema = UNDERWRITING_FIELD_SCHEMA
    
    endpoint = settings.endpoint.rstrip("/")
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": settings.api_version}
    
    _, headers = _get_auth_token_and_headers(settings)
    headers["Content-Type"] = "application/json"
    
    # Build the analyzer configuration
    analyzer_config = {
        "analyzerId": analyzer_id,
        "description": description,
        "baseAnalyzerId": "prebuilt-document",
        "config": {
            "returnDetails": True,
            "enableOcr": True,
            "enableLayout": True,
            "tableFormat": "markdown",
            "estimateFieldSourceAndConfidence": settings.enable_confidence_scores,
        },
        "fieldSchema": field_schema,
        "models": {
            "completion": "gpt-4.1",  # Use gpt-4.1-mini for cost efficiency
        },
    }
    
    logger.info("Creating/updating custom analyzer: %s", analyzer_id)
    
    resp = requests.put(
        url,
        params=params,
        headers=headers,
        json=analyzer_config,
        timeout=60,
    )
    
    # Handle 409 Conflict - analyzer already exists
    if resp.status_code == 409 and force_recreate:
        logger.info("Analyzer %s already exists, deleting and recreating...", analyzer_id)
        # Delete the existing analyzer
        delete_resp = requests.delete(url, params=params, headers=headers, timeout=30)
        if delete_resp.status_code not in (200, 202, 204, 404):
            _raise_for_status_with_detail(delete_resp)
        
        # Wait a moment for deletion to propagate
        import time
        time.sleep(2)
        
        # Recreate the analyzer
        resp = requests.put(
            url,
            params=params,
            headers=headers,
            json=analyzer_config,
            timeout=60,
        )
    
    _raise_for_status_with_detail(resp)
    
    # Check if this is an async operation
    if resp.status_code == 202:
        # Poll for completion
        result = poll_result(resp, headers, timeout_seconds=120)
        logger.info("Custom analyzer %s created/updated successfully", analyzer_id)
        return result
    
    logger.info("Custom analyzer %s created/updated successfully", analyzer_id)
    return resp.json() if resp.text else {"analyzerId": analyzer_id, "status": "succeeded"}


def delete_analyzer(
    settings: ContentUnderstandingSettings,
    analyzer_id: str,
) -> bool:
    """Delete a custom analyzer.
    
    Args:
        settings: Content Understanding settings
        analyzer_id: ID of the analyzer to delete
    
    Returns:
        True if deleted successfully
    """
    endpoint = settings.endpoint.rstrip("/")
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": settings.api_version}
    
    _, headers = _get_auth_token_and_headers(settings)
    
    resp = requests.delete(url, params=params, headers=headers, timeout=30)
    if resp.status_code == 404:
        logger.warning("Analyzer %s not found", analyzer_id)
        return False
    _raise_for_status_with_detail(resp)
    logger.info("Analyzer %s deleted successfully", analyzer_id)
    return True


def ensure_custom_analyzer_exists(
    settings: ContentUnderstandingSettings,
) -> str:
    """Ensure the custom analyzer exists, creating it if necessary.
    
    Returns:
        The analyzer ID that should be used for analysis
    """
    if not settings.enable_confidence_scores:
        # Use the default analyzer if confidence scores are disabled
        return settings.analyzer_id
    
    analyzer_id = settings.custom_analyzer_id
    
    # Check if analyzer exists
    existing = get_analyzer(settings, analyzer_id)
    if existing:
        logger.info("Custom analyzer %s already exists", analyzer_id)
        return analyzer_id
    
    # Create the analyzer
    logger.info("Creating custom analyzer %s...", analyzer_id)
    try:
        create_or_update_custom_analyzer(settings, analyzer_id)
        return analyzer_id
    except Exception as e:
        logger.warning(
            "Failed to create custom analyzer %s: %s. Falling back to default analyzer.",
            analyzer_id, str(e)
        )
        return settings.analyzer_id


def analyze_document_with_confidence(
    settings: ContentUnderstandingSettings,
    file_path: str,
    file_bytes: Optional[bytes] = None,
    output_markdown: bool = True,
    max_retries: int = 3,
    retry_backoff: float = 1.5,
) -> Dict[str, Any]:
    """Analyze a document using the custom analyzer with confidence scores.
    
    This function:
    1. Ensures the custom analyzer exists (creates if needed)
    2. Analyzes the document with confidence scoring enabled
    3. Returns the full result including confidence data
    
    Args:
        settings: Content Understanding settings
        file_path: Path to the document file (used if file_bytes not provided)
        file_bytes: Raw file content bytes (preferred for cloud storage)
        output_markdown: Whether to include markdown output
        max_retries: Number of retry attempts
        retry_backoff: Backoff multiplier between retries
    
    Returns:
        Analysis result including fields with confidence scores
    """
    # Ensure custom analyzer exists
    analyzer_id = ensure_custom_analyzer_exists(settings)
    
    if not settings.endpoint:
        raise ContentUnderstandingError(
            "Azure Content Understanding endpoint is not set."
        )

    endpoint = settings.endpoint.rstrip("/")
    
    # Get authentication
    token, headers = _get_auth_token_and_headers(settings)
    headers["Content-Type"] = "application/octet-stream"

    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
    params = {"api-version": settings.api_version}
    
    if output_markdown:
        params["outputFormat"] = "markdown"

    # Use provided bytes or read from file path
    if file_bytes is None:
        file_bytes = Path(file_path).read_bytes()

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                url,
                params=params,
                headers=headers,
                data=file_bytes,
                timeout=120,
            )
            _raise_for_status_with_detail(resp)
            
            result = poll_result(resp, headers)
            return result

        except Exception as exc:
            last_err = exc
            logger.warning(
                "Content Understanding analyze_document_with_confidence attempt %s failed: %s",
                attempt,
                str(exc),
            )
            if attempt < max_retries:
                time.sleep(retry_backoff**attempt)

    raise ContentUnderstandingError(
        f"Content Understanding analyze_document_with_confidence failed after {max_retries} attempts: {last_err}"
    )


def extract_fields_with_confidence(payload: Dict[str, Any]) -> Dict[str, FieldConfidence]:
    """Extract fields with confidence scores from the analysis result.
    
    Args:
        payload: The raw analysis result from Content Understanding
    
    Returns:
        Dictionary mapping field names to FieldConfidence objects
    """
    fields: Dict[str, FieldConfidence] = {}
    
    result = payload.get("result", {})
    
    # Fields are in result.contents[].fields or result.fields
    contents = result.get("contents", [])
    
    # Try to get fields from contents
    for content in contents:
        content_fields = content.get("fields", {})
        _process_fields(content_fields, fields)
    
    # Also check top-level result.fields
    top_fields = result.get("fields", {})
    _process_fields(top_fields, fields)
    
    # Log extraction results for debugging
    logger.info("Extracted %d fields with confidence scores", len(fields))
    for name, field in fields.items():
        logger.debug("Field %s: value=%s, confidence=%.2f", name, field.value, field.confidence)
    
    return fields


def _process_fields(
    raw_fields: Dict[str, Any],
    output: Dict[str, FieldConfidence],
    prefix: str = ""
) -> None:
    """Process raw field data and populate output with FieldConfidence objects.
    
    Args:
        raw_fields: Raw fields dictionary from API response
        output: Output dictionary to populate
        prefix: Prefix for nested field names
    """
    for field_name, field_data in raw_fields.items():
        full_name = f"{prefix}{field_name}" if not prefix else f"{prefix}.{field_name}"
        
        if not isinstance(field_data, dict):
            continue
        
        # Extract value based on field type
        value = None
        field_type = field_data.get("type", "string")
        
        # Try multiple value keys - the API may use different formats
        if field_type == "array":
            value = field_data.get("valueArray", field_data.get("value", []))
        elif field_type == "object":
            value = field_data.get("valueObject", field_data.get("value", {}))
        elif field_type == "number":
            value = field_data.get("valueNumber", field_data.get("value"))
        elif field_type == "date":
            value = field_data.get("valueDate", field_data.get("value"))
        elif field_type == "boolean":
            value = field_data.get("valueBoolean", field_data.get("value"))
        else:
            # String type - try multiple keys
            value = (
                field_data.get("valueString") or 
                field_data.get("value") or 
                field_data.get("content") or
                field_data.get("text")
            )
        
        # Extract confidence - try multiple possible keys
        confidence = (
            field_data.get("confidence") or 
            field_data.get("score") or 
            field_data.get("fieldConfidence") or
            0.0
        )
        
        # Ensure confidence is a float
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.0
        
        # Source grounding information - can be dict or string
        source = field_data.get("source", {})
        page_number = None
        bounding_box = None
        
        if isinstance(source, dict):
            page_number = source.get("pageNumber") or source.get("page")
            bounding_box = source.get("boundingBox") or source.get("polygon")
        elif isinstance(source, str):
            # If source is a string, it might contain page info
            pass
        
        # Also check for spans which may contain source text and page info
        spans = field_data.get("spans", [])
        source_text = None
        if spans and isinstance(spans, list):
            first_span = spans[0]
            if isinstance(first_span, dict):
                source_text = first_span.get("content") or first_span.get("text")
                if page_number is None:
                    page_number = first_span.get("pageNumber") or first_span.get("page")
        
        # Skip fields with no value
        if value is None or value == "" or value == [] or value == {}:
            continue
        
        # Create FieldConfidence object
        output[full_name] = FieldConfidence(
            field_name=full_name,
            value=value,
            confidence=confidence,
            page_number=page_number,
            bounding_box=bounding_box,
            source_text=source_text,
        )


def get_confidence_summary(fields: Dict[str, FieldConfidence]) -> Dict[str, Any]:
    """Generate a summary of confidence scores across all fields.
    
    Args:
        fields: Dictionary of extracted fields with confidence
    
    Returns:
        Summary statistics and categorized fields
    """
    if not fields:
        return {
            "total_fields": 0,
            "average_confidence": 0.0,
            "high_confidence_fields": [],
            "medium_confidence_fields": [],
            "low_confidence_fields": [],
        }
    
    confidences = [f.confidence for f in fields.values() if f.confidence > 0]
    
    high_threshold = 0.9
    medium_threshold = 0.7
    
    high_fields = []
    medium_fields = []
    low_fields = []
    
    for name, field in fields.items():
        field_info = {
            "name": name,
            "value": field.value,
            "confidence": field.confidence,
            "page": field.page_number,
        }
        
        if field.confidence >= high_threshold:
            high_fields.append(field_info)
        elif field.confidence >= medium_threshold:
            medium_fields.append(field_info)
        else:
            low_fields.append(field_info)
    
    return {
        "total_fields": len(fields),
        "average_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "high_confidence_fields": high_fields,
        "medium_confidence_fields": medium_fields,
        "low_confidence_fields": low_fields,
        "high_confidence_count": len(high_fields),
        "medium_confidence_count": len(medium_fields),
        "low_confidence_count": len(low_fields),
    }
