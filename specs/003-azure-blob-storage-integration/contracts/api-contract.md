# API Contract: Azure Blob Storage Integration

**Feature**: 003-azure-blob-storage-integration  
**Date**: 2025-12-08  
**Format**: OpenAPI 3.0 excerpts (changes only)

## Overview

This feature introduces **no new API endpoints**. All existing endpoints continue to work identically regardless of the configured storage backend. The changes are purely internal to the backend implementation.

## Existing Endpoints (Unchanged Behavior)

The following endpoints are unaffected from a consumer perspective:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/applications` | GET | List applications (now reads from configured backend) |
| `/applications` | POST | Create application (now writes to configured backend) |
| `/applications/{id}` | GET | Get application details |
| `/applications/{id}/analyze` | POST | Trigger document analysis |
| `/applications/{id}/files/{filename}` | GET | Retrieve uploaded file |

## Internal Contract: StorageProvider Protocol

While not an HTTP API, the storage provider protocol serves as an internal contract between the API layer and storage implementations.

### Python Protocol Definition

```python
from typing import Protocol, Optional, List, Dict, Any, runtime_checkable

@runtime_checkable
class StorageProvider(Protocol):
    """
    Protocol defining the contract for storage operations.
    
    All implementations must satisfy this interface to be used
    as the storage backend for WorkbenchIQ.
    """
    
    def save_file(
        self, 
        app_id: str, 
        filename: str, 
        content: bytes,
        public_base_url: Optional[str] = None
    ) -> str:
        """
        Save a file to storage.
        
        Args:
            app_id: Application identifier
            filename: Name of the file to save
            content: Binary content of the file
            public_base_url: Optional base URL for generating public URLs
            
        Returns:
            Storage path or URL where the file was saved
            
        Raises:
            StorageError: If the save operation fails after retries
        """
        ...
    
    def load_file(self, app_id: str, filename: str) -> Optional[bytes]:
        """
        Load a file from storage.
        
        Args:
            app_id: Application identifier
            filename: Name of the file to load
            
        Returns:
            Binary content of the file, or None if not found
            
        Raises:
            StorageError: If the load operation fails (other than not found)
        """
        ...
    
    def save_metadata(self, app_id: str, metadata: Dict[str, Any]) -> None:
        """
        Save application metadata as JSON.
        
        Args:
            app_id: Application identifier
            metadata: Dictionary to serialize as JSON
            
        Raises:
            StorageError: If the save operation fails after retries
        """
        ...
    
    def load_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Load application metadata JSON.
        
        Args:
            app_id: Application identifier
            
        Returns:
            Deserialized metadata dictionary, or None if not found
            
        Raises:
            StorageError: If the load operation fails (other than not found)
        """
        ...
    
    def list_applications(
        self, 
        persona: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all applications, optionally filtered by persona.
        
        Args:
            persona: Optional persona filter (e.g., 'underwriting', 'claims')
            
        Returns:
            List of application summary dictionaries with keys:
            - id: str
            - created_at: str
            - external_reference: Optional[str]
            - status: str
            - persona: Optional[str]
            - summary_title: Optional[str]
            
        Raises:
            StorageError: If the list operation fails
        """
        ...
    
    def save_cu_result(self, app_id: str, payload: Dict[str, Any]) -> str:
        """
        Save Content Understanding result JSON.
        
        Args:
            app_id: Application identifier
            payload: CU result dictionary to serialize
            
        Returns:
            Storage path where the result was saved
            
        Raises:
            StorageError: If the save operation fails after retries
        """
        ...
    
    def application_exists(self, app_id: str) -> bool:
        """
        Check if an application exists in storage.
        
        Args:
            app_id: Application identifier
            
        Returns:
            True if the application directory/prefix exists
        """
        ...
    
    def get_file_url(
        self, 
        app_id: str, 
        filename: str,
        public_base_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the URL for accessing a file.
        
        Args:
            app_id: Application identifier
            filename: Name of the file
            public_base_url: Optional base URL for local storage
            
        Returns:
            URL string for the file, or None if not applicable
        """
        ...
```

## Error Responses

Storage-related errors are surfaced through existing API error response patterns:

### Configuration Error (Startup)

If Azure Blob Storage is configured but credentials are missing:

```
Application fails to start with error message:
"AZURE_STORAGE_ACCOUNT_NAME is not set (required when STORAGE_BACKEND=azure_blob)"
```

### Runtime Storage Errors

Storage errors during API operations return standard HTTP error responses:

```json
{
  "detail": "Storage operation failed: <specific error message>"
}
```

| Scenario | HTTP Status | Detail Message Pattern |
|----------|-------------|----------------------|
| File not found | 404 | "Application {id} not found" |
| Auth failure | 500 | "Storage authentication failed" |
| Network timeout | 500 | "Storage operation timed out after retries" |
| Invalid container | 500 | "Storage container creation failed" |

## Configuration Contract

Environment variables serve as the configuration contract:

```yaml
# Configuration Schema (informal)
STORAGE_BACKEND:
  type: enum
  values: [local, azure_blob]
  default: local
  description: Storage backend to use

# Required when STORAGE_BACKEND=azure_blob
AZURE_STORAGE_ACCOUNT_NAME:
  type: string
  pattern: "^[a-z0-9]{3,24}$"
  description: Azure Storage account name

AZURE_STORAGE_ACCOUNT_KEY:
  type: string
  sensitive: true
  description: Azure Storage account key

# Optional
AZURE_STORAGE_CONTAINER_NAME:
  type: string
  pattern: "^[a-z0-9](?!.*--)[a-z0-9-]{1,61}[a-z0-9]$"
  default: workbenchiq-data
  description: Blob container name
```

## Backward Compatibility

This feature maintains full backward compatibility:

1. **No API changes**: All existing endpoints continue to work
2. **Default behavior unchanged**: Without new environment variables, system uses local storage
3. **Response format unchanged**: API responses have identical structure
4. **Existing data accessible**: Local data remains accessible when using local backend
