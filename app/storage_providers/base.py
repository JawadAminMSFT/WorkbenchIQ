"""Base types and protocol for storage providers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import os


class StorageBackend(Enum):
    """Supported storage backend types."""
    LOCAL = "local"
    AZURE_BLOB = "azure_blob"


@dataclass
class StorageSettings:
    """Configuration for storage backends."""
    backend: StorageBackend
    local_root: str = "data"
    
    # Azure Blob Storage settings
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_container_name: Optional[str] = None
    azure_timeout_seconds: int = 30
    azure_retry_total: int = 3
    
    # Auth mode: "default" (DefaultAzureCredential only) or "key" (account key only)
    azure_storage_auth_mode: str = "default"
    # When False (default), the provider will NOT attempt to create missing containers.
    # Set to True only in dev / migration scenarios where the identity has create perms.
    azure_storage_allow_create_container: bool = False
    
    # Optional public URL for file access
    public_base_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "StorageSettings":
        """Load storage settings from environment variables."""
        backend_str = os.getenv("STORAGE_BACKEND", "azure_blob").lower()
        try:
            backend = StorageBackend(backend_str)
        except ValueError:
            backend = StorageBackend.AZURE_BLOB
        
        auth_mode = os.getenv("AZURE_STORAGE_AUTH_MODE", "default").lower()
        if auth_mode not in ("default", "key"):
            auth_mode = "default"
        
        allow_create = os.getenv(
            "AZURE_STORAGE_ALLOW_CREATE_CONTAINER", "false"
        ).lower() in ("true", "1", "yes")
        
        return cls(
            backend=backend,
            local_root=os.getenv("UW_APP_STORAGE_ROOT", "data"),
            azure_account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
            azure_account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
            azure_container_name=os.getenv("AZURE_STORAGE_CONTAINER_NAME"),
            azure_timeout_seconds=int(os.getenv("AZURE_STORAGE_TIMEOUT_SECONDS", "30")),
            azure_retry_total=int(os.getenv("AZURE_STORAGE_RETRY_TOTAL", "3")),
            azure_storage_auth_mode=auth_mode,
            azure_storage_allow_create_container=allow_create,
            public_base_url=os.getenv("PUBLIC_FILES_BASE_URL"),
        )


@runtime_checkable
class StorageProvider(Protocol):
    """Protocol defining the interface for storage providers."""
    
    def save_file(self, app_id: str, filename: str, content: bytes) -> str:
        """Save a file and return its path/identifier."""
        ...
    
    def load_file(self, app_id: str, filename: str) -> Optional[bytes]:
        """Load file content by app_id and filename."""
        ...
    
    def load_file_by_path(self, path: str) -> Optional[bytes]:
        """Load file content by its stored path."""
        ...
    
    def get_file_url(self, app_id: str, filename: str) -> Optional[str]:
        """Get a public URL for a file, if available."""
        ...
    
    def save_metadata(self, app_id: str, metadata: Dict[str, Any]) -> None:
        """Save application metadata."""
        ...
    
    def load_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load application metadata."""
        ...
    
    def save_cu_result(self, app_id: str, payload: Dict[str, Any]) -> str:
        """Save Content Understanding result and return path."""
        ...
    
    def load_cu_result(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load Content Understanding result."""
        ...
    
    def list_applications(self) -> List[str]:
        """List all application IDs."""
        ...
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application and all its files."""
        ...
