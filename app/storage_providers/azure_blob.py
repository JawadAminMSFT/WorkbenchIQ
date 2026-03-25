"""Azure Blob Storage provider implementation.

Supports two explicit authentication methods:

1. **DefaultAzureCredential (DAC)** – Managed identity / developer credentials.
   No secrets required; relies on ``azure-identity``.  This is the default.
2. **Account key** – ``AZURE_STORAGE_ACCOUNT_NAME`` + ``AZURE_STORAGE_ACCOUNT_KEY``.

Set ``AZURE_STORAGE_AUTH_MODE`` to ``default`` (DAC) or ``key`` (account key).
There is no automatic fallback between the two methods.
"""

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

    Authentication (controlled by auth_mode):
        "default" → DefaultAzureCredential only.
        "key"     → account key only.
    """

    # Friendly labels for log messages (no secrets)
    _AUTH_LABEL_DAC = "DefaultAzureCredential"
    _AUTH_LABEL_KEY = "account_key"
    
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
        
        # Resolve blob service client using DAC-first strategy
        self._blob_service, self._resolved_auth = self._resolve_blob_service(
            settings, retry_policy
        )

        # Get container client and conditionally ensure it exists
        self._container_client = self._blob_service.get_container_client(self._container_name)
        self._ensure_container_exists()
        
        logger.info(
            "Azure Blob Storage provider ready  container='%s'  auth=%s  "
            "allow_create_container=%s",
            self._container_name,
            self._resolved_auth,
            settings.azure_storage_allow_create_container,
        )

    # ------------------------------------------------------------------
    # Auth resolution
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_blob_service(
        cls, settings: StorageSettings, retry_policy: Any
    ) -> tuple:
        """Return (BlobServiceClient, auth_label) for the configured auth mode.

        ``auth_mode == "default"`` uses DefaultAzureCredential exclusively.
        ``auth_mode == "key"`` uses account name + key exclusively.

        There is no automatic fallback between methods.
        """
        from azure.storage.blob import BlobServiceClient

        mode = settings.azure_storage_auth_mode
        timeout = settings.azure_timeout_seconds

        common_kwargs = dict(
            retry_policy=retry_policy,
            connection_timeout=timeout,
            read_timeout=timeout,
        )

        # --- explicit: key ---
        if mode == "key":
            if not (settings.azure_account_name and settings.azure_account_key):
                raise ValueError(
                    "AZURE_STORAGE_AUTH_MODE is 'key' but "
                    "AZURE_STORAGE_ACCOUNT_NAME and/or AZURE_STORAGE_ACCOUNT_KEY "
                    "are not set."
                )
            account_url = f"https://{settings.azure_account_name}.blob.core.windows.net"
            client = BlobServiceClient(
                account_url=account_url,
                credential=settings.azure_account_key,
                **common_kwargs,
            )
            return client, cls._AUTH_LABEL_KEY

        # --- default: DAC only ---
        return cls._resolve_dac(settings, common_kwargs)

    @classmethod
    def _resolve_dac(
        cls, settings: StorageSettings, common_kwargs: dict
    ) -> tuple:
        """Authenticate using DefaultAzureCredential only (no fallback)."""
        from azure.storage.blob import BlobServiceClient

        if not settings.azure_account_name:
            raise ValueError(
                "AZURE_STORAGE_AUTH_MODE is 'default' (DefaultAzureCredential) "
                "but AZURE_STORAGE_ACCOUNT_NAME is not set."
            )

        try:
            from azure.identity import DefaultAzureCredential
        except ImportError:
            raise ImportError(
                "azure-identity is required for DefaultAzureCredential auth. "
                "Install it with: pip install azure-identity  "
                "Or set AZURE_STORAGE_AUTH_MODE=key to use account key auth."
            )

        account_url = (
            f"https://{settings.azure_account_name}.blob.core.windows.net"
        )
        credential = DefaultAzureCredential()
        client = BlobServiceClient(
            account_url=account_url,
            credential=credential,
            **common_kwargs,
        )
        # Probe connectivity – use a data-plane call that only needs
        # "Storage Blob Data Contributor" (get_account_information requires
        # the management-plane "Storage Account Contributor" role).
        try:
            container = client.get_container_client(
                settings.azure_container_name
            )
            container.get_container_properties()
        except Exception as exc:
            raise ValueError(
                f"DefaultAzureCredential authentication failed: {exc}. "
                "Ensure the identity has the 'Storage Blob Data Contributor' "
                "role on the storage account, or set "
                "AZURE_STORAGE_AUTH_MODE=key to use account key."
            ) from exc

        logger.info("Authenticated via DefaultAzureCredential")
        return client, cls._AUTH_LABEL_DAC

    # ------------------------------------------------------------------
    # Container lifecycle
    # ------------------------------------------------------------------

    def _ensure_container_exists(self) -> None:
        """Optionally create the storage container.

        By default (``allow_create_container=False``), this is a no-op so
        that the identity only needs data-plane permissions (least-privilege).
        Set ``AZURE_STORAGE_ALLOW_CREATE_CONTAINER=true`` to enable auto-creation.
        """
        if not self._settings.azure_storage_allow_create_container:
            logger.debug(
                "Container auto-creation disabled; assuming '%s' exists",
                self._container_name,
            )
            return

        from azure.core.exceptions import HttpResponseError, ResourceExistsError
        
        try:
            self._container_client.create_container()
            logger.info("Created container '%s'", self._container_name)
        except ResourceExistsError:
            logger.debug("Container '%s' already exists", self._container_name)
        except HttpResponseError as exc:
            if exc.status_code == 403:
                logger.warning(
                    "Insufficient permissions to create container '%s' "
                    "(HTTP 403). Ensure the container already exists or "
                    "grant the identity the Storage Blob Data Contributor role.",
                    self._container_name,
                )
            else:
                raise
    
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
