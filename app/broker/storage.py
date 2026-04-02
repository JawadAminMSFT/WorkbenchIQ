"""
Storage for the Commercial Brokerage persona.

Supports two backends (selected by the global storage provider):
  - **local**: JSON files on disk under ``data/broker/``
  - **azure_blob**: JSON blobs under the ``broker/`` prefix in the
    configured Azure Blob Storage container.

Both modes expose the same API so the rest of the broker code is
backend-agnostic.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.broker.constants import SubmissionStatus
from app.broker.models import (
    CarrierProfile,
    Client,
    DashboardMetrics,
    Placement,
    Quote,
    Submission,
)

logger = logging.getLogger(__name__)

# Default data path for the local backend
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "broker"

# Blob prefix for the azure_blob backend
_BLOB_PREFIX = "broker"


def _is_blob_mode() -> bool:
    """Return True when the global storage provider is Azure Blob."""
    try:
        from app.storage_providers import get_storage_provider
        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        return isinstance(get_storage_provider(), AzureBlobStorageProvider)
    except Exception:
        return False


def _get_container_client():
    """Return the Azure Blob container client from the global provider."""
    from app.storage_providers import get_storage_provider
    provider = get_storage_provider()
    return provider._container_client


class BrokerStorage:
    """
    Storage service for Commercial Brokerage data.

    Blob layout (mirrors the local filesystem)::

        broker/
            clients/{client_id}.json
            submissions/{submission_id}.json
            placements/{placement_id}.json
            carriers/{carrier_id}.json
            documents/{submission_id}/{filename}
            quotes/{submission_id}/{filename}
            research-documents/{client_id}/{filename}
            research-documents/{client_id}/{doc_id}.meta.json
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._explicit_base_path = base_path

    # ------------------------------------------------------------------
    # Path / blob-key helpers
    # ------------------------------------------------------------------

    @property
    def base_path(self) -> Path:
        return self._explicit_base_path if self._explicit_base_path is not None else DATA_PATH

    @property
    def clients_path(self) -> Path:
        return self.base_path / "clients"

    @property
    def submissions_path(self) -> Path:
        return self.base_path / "submissions"

    @property
    def placements_path(self) -> Path:
        return self.base_path / "placements"

    @property
    def carriers_path(self) -> Path:
        return self.base_path / "carriers"

    def _blob_key(self, *parts: str) -> str:
        """Build a blob key from path segments."""
        return "/".join([_BLOB_PREFIX] + list(parts))

    # ------------------------------------------------------------------
    # Generic I/O (auto-dispatches to local or blob)
    # ------------------------------------------------------------------

    def _save_json(self, rel_path: str, data: Dict[str, Any]) -> None:
        """Save JSON data. *rel_path* is relative to the broker root
        (e.g. ``clients/abc.json``)."""
        payload = json.dumps(data, indent=2, default=str).encode("utf-8")
        if _is_blob_mode():
            blob_key = self._blob_key(rel_path)
            cc = _get_container_client()
            cc.get_blob_client(blob_key).upload_blob(payload, overwrite=True)
            logger.debug("Saved blob %s", blob_key)
        else:
            path = self.base_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def _load_json(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON data by relative path."""
        if _is_blob_mode():
            from azure.core.exceptions import ResourceNotFoundError
            blob_key = self._blob_key(rel_path)
            cc = _get_container_client()
            try:
                data = cc.get_blob_client(blob_key).download_blob().readall()
                return json.loads(data.decode("utf-8"))
            except ResourceNotFoundError:
                return None
        else:
            path = self.base_path / rel_path
            if not path.exists():
                return None
            return json.loads(path.read_text(encoding="utf-8"))

    def _list_json(self, folder: str) -> List[Dict[str, Any]]:
        """List all JSON objects in a folder (e.g. ``clients``)."""
        results: List[Dict[str, Any]] = []
        if _is_blob_mode():
            prefix = self._blob_key(folder) + "/"
            cc = _get_container_client()
            for blob in cc.list_blobs(name_starts_with=prefix):
                if blob.name.endswith(".json"):
                    try:
                        raw = cc.get_blob_client(blob.name).download_blob().readall()
                        results.append(json.loads(raw.decode("utf-8")))
                    except Exception:
                        logger.warning("Failed to read blob %s", blob.name)
        else:
            local = self.base_path / folder
            local.mkdir(parents=True, exist_ok=True)
            for p in sorted(local.glob("*.json")):
                try:
                    results.append(json.loads(p.read_text(encoding="utf-8")))
                except Exception:
                    logger.warning("Failed to read %s", p)
        return results

    def save_file(self, rel_path: str, content: bytes) -> str:
        """Save a binary file (document, quote PDF, etc.).

        Args:
            rel_path: Path relative to broker root (e.g.
                ``documents/{sid}/oakwood-sov.txt``)
            content: Raw file bytes

        Returns:
            The storage path/key that was written.
        """
        if _is_blob_mode():
            blob_key = self._blob_key(rel_path)
            cc = _get_container_client()
            cc.get_blob_client(blob_key).upload_blob(content, overwrite=True)
            logger.debug("Saved file blob %s", blob_key)
            return blob_key
        else:
            path = self.base_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return str(path)

    def load_file(self, rel_path: str) -> Optional[bytes]:
        """Load a binary file by relative path."""
        if _is_blob_mode():
            from azure.core.exceptions import ResourceNotFoundError
            blob_key = self._blob_key(rel_path)
            cc = _get_container_client()
            try:
                return cc.get_blob_client(blob_key).download_blob().readall()
            except ResourceNotFoundError:
                return None
        else:
            path = self.base_path / rel_path
            if not path.exists():
                return None
            return path.read_bytes()

    def list_files(self, folder: str) -> List[str]:
        """List file names in a folder."""
        if _is_blob_mode():
            prefix = self._blob_key(folder) + "/"
            cc = _get_container_client()
            names = []
            for blob in cc.list_blobs(name_starts_with=prefix):
                # Strip the prefix to get relative name
                rel = blob.name[len(prefix):]
                if rel and "/" not in rel:
                    names.append(rel)
            return sorted(names)
        else:
            local = self.base_path / folder
            if not local.exists():
                return []
            return sorted(f.name for f in local.iterdir() if f.is_file())

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def save_client(self, client: Client) -> None:
        client.updated_at = datetime.utcnow().isoformat()
        self._save_json(f"clients/{client.id}.json", asdict(client))
        logger.debug("Saved client %s", client.id)

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        return self._load_json(f"clients/{client_id}.json")

    def list_clients(self) -> List[Dict[str, Any]]:
        return self._list_json("clients")

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------

    def save_submission(self, submission: Submission) -> None:
        submission.updated_at = datetime.utcnow().isoformat()
        self._save_json(f"submissions/{submission.id}.json", asdict(submission))
        logger.debug("Saved submission %s", submission.id)

    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        return self._load_json(f"submissions/{submission_id}.json")

    def list_submissions(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._list_json("submissions")
        if client_id:
            results = [s for s in results if s.get("client_id") == client_id]
        return results

    # ------------------------------------------------------------------
    # Quotes (stored inline within their submission)
    # ------------------------------------------------------------------

    def save_quote(self, quote: Quote) -> None:
        sub_data = self.get_submission(quote.submission_id)
        if sub_data is None:
            raise ValueError(f"Submission {quote.submission_id} not found")

        quote_dict = asdict(quote)
        quotes: List[Dict[str, Any]] = sub_data.get("quotes", [])

        replaced = False
        for idx, q in enumerate(quotes):
            if q.get("id") == quote.id:
                quotes[idx] = quote_dict
                replaced = True
                break
        if not replaced:
            quotes.append(quote_dict)

        sub_data["quotes"] = quotes
        sub_data["updated_at"] = datetime.utcnow().isoformat()
        self._save_json(f"submissions/{quote.submission_id}.json", sub_data)
        logger.debug("Saved quote %s in submission %s", quote.id, quote.submission_id)

    def get_quote(self, submission_id: str, quote_id: str) -> Optional[Dict[str, Any]]:
        sub_data = self.get_submission(submission_id)
        if sub_data is None:
            return None
        for q in sub_data.get("quotes", []):
            if q.get("id") == quote_id:
                return q
        return None

    def list_quotes_for_submission(self, submission_id: str) -> List[Dict[str, Any]]:
        sub_data = self.get_submission(submission_id)
        if sub_data is None:
            return []
        return sub_data.get("quotes", [])

    # ------------------------------------------------------------------
    # Placements
    # ------------------------------------------------------------------

    def save_placement(self, placement: Placement) -> None:
        self._save_json(f"placements/{placement.id}.json", asdict(placement))
        logger.debug("Saved placement %s", placement.id)

    def get_placement(self, placement_id: str) -> Optional[Dict[str, Any]]:
        return self._load_json(f"placements/{placement_id}.json")

    # ------------------------------------------------------------------
    # Carrier Profiles
    # ------------------------------------------------------------------

    def save_carrier_profile(self, profile: CarrierProfile) -> None:
        self._save_json(f"carriers/{profile.id}.json", asdict(profile))
        logger.debug("Saved carrier profile %s (%s)", profile.id, profile.carrier_name)

    def get_carrier_profile(self, carrier_id: str) -> Optional[Dict[str, Any]]:
        return self._load_json(f"carriers/{carrier_id}.json")

    def list_carrier_profiles(self) -> List[Dict[str, Any]]:
        return self._list_json("carriers")

    def get_carrier_profile_by_name(self, carrier_name: str) -> Optional[Dict[str, Any]]:
        carrier_name_lower = carrier_name.lower()
        for profile in self.list_carrier_profiles():
            if profile.get("carrier_name", "").lower() == carrier_name_lower:
                return profile
        return None

    # ------------------------------------------------------------------
    # Dashboard metrics (computed on the fly)
    # ------------------------------------------------------------------

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        clients = self.list_clients()
        submissions = self.list_submissions()

        total_accounts = len(clients)
        open_statuses = {
            SubmissionStatus.DRAFT.value,
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.QUOTED.value,
        }
        open_submissions = sum(
            1 for s in submissions if s.get("status") in open_statuses
        )

        bound_premium = 0.0
        for s in submissions:
            if s.get("status") == SubmissionStatus.BOUND.value:
                for q in s.get("quotes", []):
                    raw = q.get("fields", {}).get("annual_premium", "")
                    try:
                        bound_premium += float(str(raw).replace("$", "").replace(",", ""))
                    except (ValueError, TypeError):
                        pass

        cutoff = (datetime.utcnow() + timedelta(days=90)).isoformat()
        now_iso = datetime.utcnow().isoformat()
        renewals_due = 0
        for c in clients:
            rd = c.get("renewal_date")
            if rd and now_iso <= rd <= cutoff:
                renewals_due += 1

        stale_cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        stale = sum(
            1
            for s in submissions
            if s.get("status") in open_statuses
            and s.get("updated_at", "") < stale_cutoff
        )

        metrics = DashboardMetrics(
            total_accounts=total_accounts,
            total_bound_premium=f"${bound_premium:,.2f}",
            open_submissions=open_submissions,
            renewals_due_90_days=renewals_due,
            stale_submissions=stale,
        )
        return asdict(metrics)
