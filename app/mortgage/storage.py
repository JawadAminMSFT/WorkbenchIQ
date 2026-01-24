"""
JSON storage for mortgage applications.

Stores mortgage case data in the data/applications directory structure.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Default data path - can be overridden in tests
DATA_PATH = Path(__file__).parent.parent.parent / "data"


class MortgageStorage:
    """
    Storage service for mortgage application data.
    
    File structure:
        data/applications/{case_id}/
            metadata.json          - Case metadata and status
            content_understanding.json - Raw CU extraction results
            provenance.json        - Field provenance tracking
            calculations.json      - Calculation results with formulas
            findings.json          - Policy engine findings
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize storage.
        
        Args:
            base_path: Base path for data storage (defaults to DATA_PATH)
        """
        # Store explicit base_path if provided, otherwise use None to signal using module DATA_PATH
        self._explicit_base_path = base_path
    
    @property
    def base_path(self) -> Path:
        """Get base path, using module-level DATA_PATH if not explicitly set."""
        return self._explicit_base_path if self._explicit_base_path is not None else DATA_PATH
    
    @property
    def applications_path(self) -> Path:
        """Get applications path."""
        return self.base_path / "applications"
    
    def _get_case_dir(self, case_id: str) -> Path:
        """Get the directory path for a case."""
        return self.applications_path / case_id
    
    def _ensure_case_dir(self, case_id: str) -> Path:
        """Ensure case directory exists."""
        case_dir = self._get_case_dir(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir
    
    def save_mortgage_case(self, case_id: str, case_data: Dict[str, Any]) -> None:
        """
        Save mortgage case metadata.
        
        Args:
            case_id: Unique case identifier
            case_data: Case data to save
        """
        case_dir = self._ensure_case_dir(case_id)
        
        # Wrap in mortgage_case if not already
        if "mortgage_case" not in case_data:
            case_data = {"mortgage_case": case_data}
        
        # Add timestamps
        case_data["mortgage_case"]["updated_at"] = datetime.utcnow().isoformat()
        if "created_at" not in case_data["mortgage_case"]:
            case_data["mortgage_case"]["created_at"] = datetime.utcnow().isoformat()
        
        metadata_path = case_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(case_data, f, indent=2, default=str)
    
    def get_mortgage_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Load mortgage case metadata.
        
        Args:
            case_id: Unique case identifier
            
        Returns:
            Case data or None if not found
        """
        metadata_path = self._get_case_dir(case_id) / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path) as f:
            return json.load(f)
    
    def update_mortgage_case(self, case_id: str, updates: Dict[str, Any]) -> None:
        """
        Update mortgage case with new data.
        
        Args:
            case_id: Unique case identifier
            updates: Fields to update
        """
        existing = self.get_mortgage_case(case_id)
        
        if existing:
            # Merge updates into mortgage_case
            if "mortgage_case" in existing:
                existing["mortgage_case"].update(updates)
            else:
                existing.update(updates)
            self.save_mortgage_case(case_id, existing)
        else:
            # Create new case with updates
            self.save_mortgage_case(case_id, updates)
    
    def save_content_understanding(
        self,
        case_id: str,
        extraction_result: Dict[str, Any]
    ) -> None:
        """
        Save Content Understanding extraction results.
        
        Args:
            case_id: Unique case identifier
            extraction_result: Raw CU extraction results
        """
        case_dir = self._get_case_dir(case_id)
        cu_path = case_dir / "content_understanding.json"
        
        with open(cu_path, "w") as f:
            json.dump(extraction_result, f, indent=2, default=str)
    
    def get_content_understanding(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Load Content Understanding extraction results.
        
        Args:
            case_id: Unique case identifier
            
        Returns:
            Extraction results or None
        """
        cu_path = self._get_case_dir(case_id) / "content_understanding.json"
        
        if not cu_path.exists():
            return None
        
        with open(cu_path) as f:
            return json.load(f)
    
    def save_provenance(self, case_id: str, provenance: Dict[str, Any]) -> None:
        """
        Save field provenance data.
        
        Args:
            case_id: Unique case identifier
            provenance: Provenance tracking data
        """
        case_dir = self._get_case_dir(case_id)
        prov_path = case_dir / "provenance.json"
        
        with open(prov_path, "w") as f:
            json.dump(provenance, f, indent=2, default=str)
    
    def save_calculations(self, case_id: str, calculations: Dict[str, Any]) -> None:
        """
        Save calculation results.
        
        Args:
            case_id: Unique case identifier
            calculations: Calculation results with provenance
        """
        case_dir = self._get_case_dir(case_id)
        calc_path = case_dir / "calculations.json"
        
        with open(calc_path, "w") as f:
            json.dump(calculations, f, indent=2, default=str)
    
    def save_findings(self, case_id: str, findings: Dict[str, Any]) -> None:
        """
        Save policy engine findings.
        
        Args:
            case_id: Unique case identifier
            findings: Policy evaluation findings
        """
        case_dir = self._get_case_dir(case_id)
        findings_path = case_dir / "findings.json"
        
        with open(findings_path, "w") as f:
            json.dump(findings, f, indent=2, default=str)
    
    def list_cases(self) -> list[str]:
        """
        List all mortgage case IDs.
        
        Returns:
            List of case IDs
        """
        if not self.applications_path.exists():
            return []
        
        return [
            d.name for d in self.applications_path.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a mortgage case and all associated files.
        
        Args:
            case_id: Unique case identifier
            
        Returns:
            True if deleted, False if not found
        """
        import shutil
        
        case_dir = self._get_case_dir(case_id)
        if case_dir.exists():
            shutil.rmtree(case_dir)
            return True
        return False
