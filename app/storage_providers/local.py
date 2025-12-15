"""Local filesystem storage provider implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.storage_providers.base import StorageSettings

logger = logging.getLogger(__name__)


class LocalStorageProvider:
    """Storage provider implementation using local filesystem.
    
    This provider stores application data in the local filesystem:
    
        {storage_root}/applications/{app_id}/files/{filename}
        {storage_root}/applications/{app_id}/metadata.json
        {storage_root}/applications/{app_id}/content_understanding.json
    """
    
    def __init__(
        self, 
        settings: StorageSettings,
        public_base_url: Optional[str] = None
    ) -> None:
        """Initialize the local storage provider.
        
        Args:
            settings: Storage settings containing local root path.
            public_base_url: Optional base URL for public file access.
        """
        self._settings = settings
        # Resolve to absolute path to ensure file paths are always absolute
        self._storage_root = Path(settings.local_root).resolve()
        self._public_base_url = public_base_url or settings.public_base_url
        
        # Ensure storage root exists
        self._storage_root.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Initialized Local Storage provider at '%s'",
            self._storage_root
        )
    
    def _get_application_dir(self, app_id: str) -> Path:
        """Get the directory path for an application."""
        app_dir = self._storage_root / "applications" / app_id
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    
    def _get_files_dir(self, app_id: str) -> Path:
        """Get the files directory path for an application."""
        files_dir = self._get_application_dir(app_id) / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        return files_dir
    
    def save_file(self, app_id: str, filename: str, content: bytes) -> str:
        """Save a file to local filesystem.
        
        Returns:
            Absolute file path where the file was saved.
        """
        files_dir = self._get_files_dir(app_id)
        file_path = files_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.debug("Saved file to local: %s", file_path)
        return str(file_path)
    
    def load_file(self, app_id: str, filename: str) -> Optional[bytes]:
        """Load a file from local filesystem."""
        file_path = self._get_files_dir(app_id) / filename
        
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return None
        
        return file_path.read_bytes()
    
    def load_file_by_path(self, path: str) -> Optional[bytes]:
        """Load file content by its stored path."""
        file_path = Path(path)
        
        # If relative, resolve against storage root
        if not file_path.is_absolute():
            file_path = self._storage_root / path
        
        if not file_path.exists():
            logger.warning("File not found at path: %s", file_path)
            return None
        
        return file_path.read_bytes()
    
    def get_file_url(self, app_id: str, filename: str) -> Optional[str]:
        """Get a public URL for a file, if available."""
        if not self._public_base_url:
            return None
        return f"{self._public_base_url.rstrip('/')}/applications/{app_id}/files/{filename}"
    
    def save_metadata(self, app_id: str, metadata: Dict[str, Any]) -> None:
        """Save application metadata."""
        app_dir = self._get_application_dir(app_id)
        meta_path = app_dir / "metadata.json"
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug("Saved metadata for app %s", app_id)
    
    def load_metadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load application metadata."""
        app_dir = self._get_application_dir(app_id)
        meta_path = app_dir / "metadata.json"
        
        if not meta_path.exists():
            return None
        
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_cu_result(self, app_id: str, payload: Dict[str, Any]) -> str:
        """Save Content Understanding result."""
        app_dir = self._get_application_dir(app_id)
        cu_path = app_dir / "content_understanding.json"
        
        with open(cu_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        logger.debug("Saved CU result for app %s", app_id)
        return str(cu_path)
    
    def load_cu_result(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Load Content Understanding result."""
        app_dir = self._get_application_dir(app_id)
        cu_path = app_dir / "content_understanding.json"
        
        if not cu_path.exists():
            return None
        
        with open(cu_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_applications(self) -> List[str]:
        """List all application IDs."""
        apps_dir = self._storage_root / "applications"
        if not apps_dir.exists():
            return []
        
        return [
            d.name for d in apps_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]
    
    def delete_application(self, app_id: str) -> bool:
        """Delete an application and all its files."""
        import shutil
        
        app_dir = self._storage_root / "applications" / app_id
        if not app_dir.exists():
            return False
        
        shutil.rmtree(app_dir)
        logger.info("Deleted application %s", app_id)
        return True
