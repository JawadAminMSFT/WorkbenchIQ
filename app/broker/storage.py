"""
JSON-file storage for the Commercial Brokerage persona.

Stores clients, submissions, quotes, placements, and carrier profiles
under the ``data/broker/`` directory tree.
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

# Default data path – can be overridden in tests
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "broker"


class BrokerStorage:
    """
    Storage service for Commercial Brokerage data.

    File structure::

        data/broker/
            clients/{client_id}.json
            submissions/{submission_id}.json
            placements/{placement_id}.json
            carriers/{carrier_id}.json
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        Initialize storage.

        Args:
            base_path: Base path for broker data (defaults to DATA_PATH).
        """
        self._explicit_base_path = base_path

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    @property
    def base_path(self) -> Path:
        """Get base path, using module-level DATA_PATH if not explicitly set."""
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

    def _ensure_dir(self, path: Path) -> Path:
        """Create directory if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ------------------------------------------------------------------
    # Generic I/O
    # ------------------------------------------------------------------

    def _save_json(self, path: Path, data: Dict[str, Any]) -> None:
        self._ensure_dir(path.parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def save_client(self, client: Client) -> None:
        """Save or update a client record."""
        client.updated_at = datetime.utcnow().isoformat()
        path = self.clients_path / f"{client.id}.json"
        self._save_json(path, asdict(client))
        logger.debug("Saved client %s", client.id)

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load a client by ID. Returns ``None`` if not found."""
        return self._load_json(self.clients_path / f"{client_id}.json")

    def list_clients(self) -> List[Dict[str, Any]]:
        """Return all client records."""
        self._ensure_dir(self.clients_path)
        results: List[Dict[str, Any]] = []
        for p in sorted(self.clients_path.glob("*.json")):
            data = self._load_json(p)
            if data is not None:
                results.append(data)
        return results

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------

    def save_submission(self, submission: Submission) -> None:
        """Save or update a submission record."""
        submission.updated_at = datetime.utcnow().isoformat()
        path = self.submissions_path / f"{submission.id}.json"
        self._save_json(path, asdict(submission))
        logger.debug("Saved submission %s", submission.id)

    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Load a submission by ID."""
        return self._load_json(self.submissions_path / f"{submission_id}.json")

    def list_submissions(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return submissions, optionally filtered by client_id."""
        self._ensure_dir(self.submissions_path)
        results: List[Dict[str, Any]] = []
        for p in sorted(self.submissions_path.glob("*.json")):
            data = self._load_json(p)
            if data is None:
                continue
            if client_id and data.get("client_id") != client_id:
                continue
            results.append(data)
        return results

    # ------------------------------------------------------------------
    # Quotes (stored inline within their submission)
    # ------------------------------------------------------------------

    def save_quote(self, quote: Quote) -> None:
        """Save or update a quote inside its parent submission."""
        sub_data = self.get_submission(quote.submission_id)
        if sub_data is None:
            raise ValueError(f"Submission {quote.submission_id} not found")

        quote_dict = asdict(quote)
        quotes: List[Dict[str, Any]] = sub_data.get("quotes", [])

        # Replace existing or append
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
        path = self.submissions_path / f"{quote.submission_id}.json"
        self._save_json(path, sub_data)
        logger.debug("Saved quote %s in submission %s", quote.id, quote.submission_id)

    def get_quote(self, submission_id: str, quote_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single quote by submission + quote ID."""
        sub_data = self.get_submission(submission_id)
        if sub_data is None:
            return None
        for q in sub_data.get("quotes", []):
            if q.get("id") == quote_id:
                return q
        return None

    def list_quotes_for_submission(self, submission_id: str) -> List[Dict[str, Any]]:
        """Return all quotes for a given submission."""
        sub_data = self.get_submission(submission_id)
        if sub_data is None:
            return []
        return sub_data.get("quotes", [])

    # ------------------------------------------------------------------
    # Placements
    # ------------------------------------------------------------------

    def save_placement(self, placement: Placement) -> None:
        """Save or update a placement record."""
        path = self.placements_path / f"{placement.id}.json"
        self._save_json(path, asdict(placement))
        logger.debug("Saved placement %s", placement.id)

    def get_placement(self, placement_id: str) -> Optional[Dict[str, Any]]:
        """Load a placement by ID."""
        return self._load_json(self.placements_path / f"{placement_id}.json")

    # ------------------------------------------------------------------
    # Carrier Profiles
    # ------------------------------------------------------------------

    def save_carrier_profile(self, profile: CarrierProfile) -> None:
        """Save or update a carrier profile."""
        path = self.carriers_path / f"{profile.id}.json"
        self._save_json(path, asdict(profile))
        logger.debug("Saved carrier profile %s (%s)", profile.id, profile.carrier_name)

    def get_carrier_profile(self, carrier_id: str) -> Optional[Dict[str, Any]]:
        """Load a carrier profile by ID."""
        return self._load_json(self.carriers_path / f"{carrier_id}.json")

    def list_carrier_profiles(self) -> List[Dict[str, Any]]:
        """Return all carrier profiles."""
        self._ensure_dir(self.carriers_path)
        results: List[Dict[str, Any]] = []
        for p in sorted(self.carriers_path.glob("*.json")):
            data = self._load_json(p)
            if data is not None:
                results.append(data)
        return results

    def get_carrier_profile_by_name(self, carrier_name: str) -> Optional[Dict[str, Any]]:
        """Load a carrier profile by carrier name (case-insensitive).
        
        Args:
            carrier_name: Name of the carrier to search for
            
        Returns:
            Carrier profile dict or None if not found
        """
        carrier_name_lower = carrier_name.lower()
        all_profiles = self.list_carrier_profiles()
        for profile in all_profiles:
            if profile.get("carrier_name", "").lower() == carrier_name_lower:
                return profile
        return None

    # ------------------------------------------------------------------
    # Dashboard metrics (computed on the fly)
    # ------------------------------------------------------------------

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Compute dashboard metrics from stored data."""
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

        # Total bound premium
        bound_premium = 0.0
        for s in submissions:
            if s.get("status") == SubmissionStatus.BOUND.value:
                for q in s.get("quotes", []):
                    raw = q.get("fields", {}).get("annual_premium", "")
                    try:
                        bound_premium += float(str(raw).replace("$", "").replace(",", ""))
                    except (ValueError, TypeError):
                        pass

        # Renewals due within 90 days
        cutoff = (datetime.utcnow() + timedelta(days=90)).isoformat()
        now_iso = datetime.utcnow().isoformat()
        renewals_due = 0
        for c in clients:
            rd = c.get("renewal_date")
            if rd and now_iso <= rd <= cutoff:
                renewals_due += 1

        # Stale submissions (no update in >7 days)
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
