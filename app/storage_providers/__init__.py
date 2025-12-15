"""Storage providers package.

This package provides pluggable storage backends for application data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

from app.storage_providers.base import StorageBackend, StorageSettings, StorageProvider

if TYPE_CHECKING:
    from app.storage_providers.azure_blob import AzureBlobStorageProvider
    from app.storage_providers.local import LocalStorageProvider

logger = logging.getLogger(__name__)

# Global storage provider instance (singleton pattern)
_storage_provider: Optional[Union["LocalStorageProvider", "AzureBlobStorageProvider"]] = None


def init_storage_provider(settings: Optional[StorageSettings] = None) -> None:
    """Initialize the global storage provider.
    
    Args:
        settings: Storage settings. If None, loads from environment.
    """
    global _storage_provider
    
    if settings is None:
        settings = StorageSettings.from_env()
    
    if settings.backend == StorageBackend.AZURE_BLOB:
        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        _storage_provider = AzureBlobStorageProvider(settings)
        logger.info("Initialized Azure Blob Storage provider")
    else:
        from app.storage_providers.local import LocalStorageProvider
        _storage_provider = LocalStorageProvider(settings)
        logger.info("Initialized Local Storage provider")


def get_storage_provider() -> Union["LocalStorageProvider", "AzureBlobStorageProvider"]:
    """Get the initialized storage provider.
    
    Returns:
        The storage provider instance.
        
    Raises:
        RuntimeError: If the storage provider has not been initialized.
    """
    if _storage_provider is None:
        raise RuntimeError(
            "Storage provider not initialized. "
            "Call init_storage_provider() first."
        )
    return _storage_provider


def reset_storage_provider() -> None:
    """Reset the storage provider (useful for testing)."""
    global _storage_provider
    _storage_provider = None


__all__ = [
    "StorageBackend",
    "StorageSettings",
    "StorageProvider",
    "init_storage_provider",
    "get_storage_provider",
    "reset_storage_provider",
]
