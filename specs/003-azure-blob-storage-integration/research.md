# Research: Azure Blob Storage Integration

**Feature**: 003-azure-blob-storage-integration  
**Date**: 2025-12-08  
**Purpose**: Resolve technical unknowns and establish best practices before implementation

## Research Tasks

### 1. Azure Blob Storage Python SDK Best Practices

**Decision**: Use `azure-storage-blob` SDK with `BlobServiceClient` as the primary entry point.

**Rationale**: 
- Official Microsoft SDK with active maintenance
- Built-in retry policies (ExponentialRetry, LinearRetry) align with FR-010
- Native support for storage account key authentication per user requirements
- Synchronous API preferred (application is not async-first)

**Key Findings**:
```python
from azure.storage.blob import BlobServiceClient, ExponentialRetry

# Create client with retry policy
retry = ExponentialRetry(initial_backoff=10, increment_base=4, retry_total=3)
blob_service_client = BlobServiceClient(
    account_url=f"https://{account_name}.blob.core.windows.net",
    credential=account_key,  # Storage account key
    retry_policy=retry
)
```

**Alternatives Considered**:
- `azure-storage-blob[aio]` (async): Rejected because FastAPI endpoints currently use sync patterns
- Connection strings: Rejected in favor of account URL + key for clearer configuration

### 2. Retry Policy Configuration

**Decision**: Use `ExponentialRetry` with 3 retries, 10s initial backoff, 30s timeout.

**Rationale**:
- Exponential backoff prevents overwhelming services during recovery (per MS best practices)
- 3 retries aligns with SC-005 requirement
- 10s initial backoff + exponential growth provides reasonable wait times: 10s → 14s → 22s
- 30s timeout per operation (FR-011) accommodates typical document sizes

**Configuration**:
```python
from azure.storage.blob import ExponentialRetry

retry_policy = ExponentialRetry(
    initial_backoff=10,      # First retry after 10 seconds
    increment_base=4,        # Exponential factor
    retry_total=3,           # Maximum 3 retries
    random_jitter_range=3    # ±3s jitter to prevent thundering herd
)
```

**SDK Default Behavior**:
- Automatically retries: 408, 429, 500, 502, 503, 504
- Does NOT retry: 4xx client errors (400, 401, 403, 404)
- This aligns with our requirement to surface auth errors immediately

### 3. Storage Provider Abstraction Pattern

**Decision**: Use Python Protocol (typing.Protocol) for storage abstraction, not ABC.

**Rationale**:
- Protocol provides structural typing (duck typing) which is more Pythonic
- No inheritance required - existing `storage.py` functions can be wrapped
- Easier testing with mock implementations
- Aligns with existing WorkbenchIQ code style (dataclasses, type hints)

**Interface Design**:
```python
from typing import Protocol, Optional, List, Dict, Any

class StorageProvider(Protocol):
    """Protocol defining storage operations for WorkbenchIQ."""
    
    def save_file(self, app_id: str, filename: str, content: bytes) -> str:
        """Save file and return the storage path/URL."""
        ...
    
    def load_file(self, app_id: str, filename: str) -> Optional[bytes]:
        """Load file content or return None if not found."""
        ...
    
    def save_metadata(self, app_id: str, metadata: Dict[str, Any]) -> None:
        """Save application metadata JSON."""
        ...
    
    def load_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load application metadata or return None."""
        ...
    
    def list_applications(self, persona: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all applications, optionally filtered by persona."""
        ...
    
    def save_cu_result(self, app_id: str, payload: Dict[str, Any]) -> str:
        """Save Content Understanding result JSON."""
        ...
    
    def application_exists(self, app_id: str) -> bool:
        """Check if application directory/prefix exists."""
        ...
```

**Alternatives Considered**:
- ABC (Abstract Base Class): Rejected as overly formal for two implementations
- Direct blob client injection: Rejected as it couples storage.py to Azure SDK

### 4. Container Creation Strategy

**Decision**: Create container on first write operation with `create_if_not_exists()`.

**Rationale**:
- `ContainerClient.create_if_not_exists()` is idempotent and handles race conditions
- No startup penalty if container already exists
- Avoids requiring pre-deployment infrastructure setup

**Implementation**:
```python
container_client = blob_service_client.get_container_client(container_name)
container_client.create_if_not_exists()
```

### 5. Blob Path Structure

**Decision**: Mirror local filesystem structure exactly in blob storage.

**Rationale**:
- Simplifies implementation (same path logic for both backends)
- Enables potential future migration between backends
- Maintains existing application ID structure

**Path Mapping**:
| Local Path | Blob Path |
|------------|-----------|
| `data/applications/{app_id}/files/{filename}` | `applications/{app_id}/files/{filename}` |
| `data/applications/{app_id}/metadata.json` | `applications/{app_id}/metadata.json` |
| `data/applications/{app_id}/content_understanding.json` | `applications/{app_id}/content_understanding.json` |

Note: The `data/` prefix is a local storage root concept; blob storage uses container as root.

### 6. Configuration Loading Pattern

**Decision**: Extend existing `load_settings()` in `config.py` with new `StorageSettings` dataclass.

**Rationale**:
- Maintains consistency with existing configuration pattern
- Single source of truth for all settings
- Validation integrated into existing `validate_settings()` function

**Environment Variables**:
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_BACKEND` | No | `local` | Backend type: `local` or `azure_blob` |
| `AZURE_STORAGE_ACCOUNT_NAME` | If azure_blob | - | Storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | If azure_blob | - | Storage account key |
| `AZURE_STORAGE_CONTAINER_NAME` | No | `workbenchiq-data` | Blob container name |

### 7. Error Handling Strategy

**Decision**: Let Azure SDK exceptions propagate; handle at API layer.

**Rationale**:
- Azure SDK raises `AzureError` hierarchy with specific error codes
- Storage provider should not mask errors (Constitution Principle IV requires actionable messages)
- FastAPI error handlers can convert to appropriate HTTP responses

**Key Exception Types**:
- `ResourceNotFoundError`: 404 - blob or container not found
- `ResourceExistsError`: 409 - conflict during creation
- `ClientAuthenticationError`: 401/403 - invalid credentials
- `ServiceRequestError`: Network/connection errors (retried automatically)

## Dependencies

### New Package Requirements

```
azure-storage-blob>=12.19.0
```

**Version Rationale**: 12.19.0+ includes latest retry policy improvements and Python 3.10+ support.

### No Additional Dependencies Needed

- `tenacity`: Not needed - Azure SDK has built-in retry
- `azure-identity`: Not needed - using storage account key authentication per user requirement

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK version incompatibility | Low | Medium | Pin to specific minor version in requirements.txt |
| Network partition during upload | Medium | Medium | Retry policy handles; document partial upload behavior |
| Container name collision | Low | Low | Use unique default name; validate on startup |
| Large file performance | Low | Low | SDK handles chunking automatically; 100MB files tested |

## References

- [Azure Storage Blob Python SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/storage-blob-readme)
- [Implement a retry policy with Python](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-retry-policy-python)
- [Azure SDK Error Handling](https://learn.microsoft.com/en-us/azure/developer/python/sdk/fundamentals/errors)
- [HTTP Pipeline and Retries](https://learn.microsoft.com/en-us/azure/developer/python/sdk/fundamentals/http-pipeline-retries)
