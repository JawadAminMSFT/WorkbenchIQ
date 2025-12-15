"""Azure Blob Storage provider implementation."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.storage_providers.base import StorageSettings

logger = logging.getLogger(__name__)


class AzureBlobStorageProvider:
    """Storage provider implementation using Azure Blob Storage.
    
    This provider stores application data in Azure Blob Storage:
    
        {container}/applications/{app_id}/files/{filename}
        {container}/applications/{app_id}/metadata.json
        {container}/applications/{app_id}/content_understanding.json
    """
    
    def __init__(
        self, 
        settings: StorageSettings,
        public_base_url: Optional[str] = None
    ) -> None:
        """Initialize the Azure Blob Storage provider.
        
        Args:
            settings: Storage settings containing Azure credentials.
            public_base_url: Optional base URL for public file access.
        """
        try:
            from azure.storage.blob import BlobServiceClient, ExponentialRetry
        except ImportError:
            raise ImportError(
                "azure-storage-blob is required for Azure Blob Storage. "
                "Install it with: pip install azure-storage-blob"
            )
        
        self._settings = settings
        self._container_name = settings.azure_container_name
        self._public_base_url = public_base_url or settings.public_base_url
        
        if not self._container_name:
            raise ValueError("AZURE_STORAGE_CONTAINER_NAME is required")
        
        # Configure retry policy
        retry_policy = ExponentialRetry(
            initial_backoff=10,
            increment_base=4,
            retry_total=settings.azure_retry_total
        )
        
        # Create blob service client
        if settings.azure_connection_string:
            self._blob_service = BlobServiceClient.from_connection_string(
                settings.azure_connection_string,
                retry_policy=retry_policy,
                connection_timeout=settings.azure_timeout_seconds,
                read_timeout=settings.azure_timeout_seconds,
            )
        elif settings.azure_account_name and settings.azure_account_key:
            account_url = f"https://{settings.azure_account_name}.blob.core.windows.net"
            self._blob_service = BlobServiceClient(
                account_url=account_url,
                credential=settings.azure_account_key,
                retry_policy=retry_policy,
                connection_timeout=settings.azure_timeout_seconds,
                read_timeout=settings.azure_timeout_seconds,
            )
        else:
            raise ValueError(
                "Azure Blob Storage requires either AZURE_STORAGE_CONNECTION_STRING "
                "or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY"
            )
        
        # Get container client and ensure it exists
        self._container_client = self._blob_service.get_container_client(self._container_name)
        self._ensure_container_exists()
        
        logger.info(
            "Initialized Azure Blob Storage provider for container '%s'",
            self._container_name
        )
    
    def _ensure_container_exists(self) -> None:
        """Ensure the storage container exists, creating it if necessary."""
        from azure.core.exceptions import ResourceExistsError
        
        try:
            self._container_client.create_container()
            logger.info("Created container '%s'", self._container_name)
        except ResourceExistsError:
            logger.debug("Container '%s' already exists", self._container_name)
    
    def _get_blob_path(self, app_id: str, *parts: str) -> str:
        """Construct a blob path for an application."""
        return "/".join(["applications", app_id] + list(parts))
    
    def save_file(self, app_id: str, filename: str, content: bytes) -> str:
        """Save a file to Azure Blob Storage.
        
        Returns:
            Blob path where the file was saved.
        """
        blob_path = self._get_blob_path(app_id, "files", filename)
        blob_client = self._container_client.get_blob_client(blob_path)
        
        blob_client.upload_blob(content, overwrite=True)
        
        logger.debug("Saved file to blob: %s", blob_path)
        return blob_path
    
    def load_file(self, app_id: str, filename: str) -> Optional[bytes]:
        """Load a file from Azure Blob Storage."""
        blob_path = self._get_blob_path(app_id, "files", filename)
        return self._download_blob(blob_path)
    
    def load_file_by_path(self, path: str) -> Optional[bytes]:
        """Load file content by its stored blob path."""
        return self._download_blob(path)
    
    def _download_blob(self, blob_path: str) -> Optional[bytes]:
        """Download blob content by path."""
        from azure.core.exceptions import ResourceNotFoundError
        
        blob_client = self._container_client.get_blob_client(blob_path)
        
        try:
            download = blob_client.download_blob()
            return download.readall()
        except ResourceNotFoundError:
            logger.warning("Blob not found: %s", blob_path)
            return None
    
    def get_file_url(self, app_id: str, filename: str) -> Optional[str]:
        """Get a public URL for a file, if available."""
        if self._public_base_url:
            blob_path = self._get_blob_path(app_id, "files", filename)
            return f"{self._public_base_url.rstrip('/')}/{blob_path}"
        
        # Return direct blob URL (requires public access or SAS token)
        blob_path = self._get_blob_path(app_id, "files", filename)
        return f"https://{self._settings.azure_account_name}.blob.core.windows.net/{self._container_name}/{blob_path}"
    
    def save_metadata(self, app_id: str, metadata: Dict[str, Any]) -> None:
        """Save application metadata."""
        blob_path = self._get_blob_path(app_id, "metadata.json")
        content = json.dumps(metadata, indent=2).encode("utf-8")
        
        blob_client = self._container_client.get_blob_client(blob_path)
        blob_client.upload_blob(content, overwrite=True)
        
        logger.debug("Saved metadata for app %s", app_id)
    
    def load_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load application metadata."""
        blob_path = self._get_blob_path(app_id, "metadata.json")
        content = self._download_blob(blob_path)
        
        if content is None:
            return None
        
        return json.loads(content.decode("utf-8"))
    
    def save_cu_result(self, app_id: str, payload: Dict[str, Any]) -> str:
        """Save Content Understanding result."""
        blob_path = self._get_blob_path(app_id, "content_understanding.json")
        content = json.dumps(payload, indent=2).encode("utf-8")
        
        blob_client = self._container_client.get_blob_client(blob_path)
        blob_client.upload_blob(content, overwrite=True)
        
        logger.debug("Saved CU result for app %s", app_id)
        return blob_path
    
    def load_cu_result(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load Content Understanding result."""
        blob_path = self._get_blob_path(app_id, "content_understanding.json")
        content = self._download_blob(blob_path)
        
        if content is None:
            return None
        
        return json.loads(content.decode("utf-8"))
    
    def list_applications(self) -> List[str]:
        """List all application IDs."""
        prefix = "applications/"
        app_ids = set()
        
        for blob in self._container_client.list_blobs(name_starts_with=prefix):
            # Extract app_id from path like "applications/{app_id}/..."
            parts = blob.name.split("/")
            if len(parts) >= 2:
                app_ids.add(parts[1])
        
        return list(app_ids)
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application and all its blobs."""
        prefix = self._get_blob_path(app_id, "")
        deleted = False
        
        for blob in self._container_client.list_blobs(name_starts_with=prefix):
            blob_client = self._container_client.get_blob_client(blob.name)
            blob_client.delete_blob()
            deleted = True
        
        if deleted:
            logger.info("Deleted application %s", app_id)
        
        return deleted
