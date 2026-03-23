"""
Customer 360 — Unified Data Layer.

Provides a cross-persona customer view by aggregating applications
linked via external_reference. Stores customer profiles as JSON in
data/customers/{customer_id}/profile.json.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.storage import list_applications, load_application

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class CustomerProfile:
    """Core customer profile linking applications across personas."""
    id: str
    name: str
    date_of_birth: str
    email: str
    phone: str
    address: str
    customer_since: str
    risk_tier: str  # "low", "medium", "high"
    tags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CustomerJourneyEvent:
    """A single event in the customer journey timeline."""
    date: str
    persona: str
    application_id: str
    event_type: str  # application_submitted, claim_filed, underwriting_complete, etc.
    title: str
    summary: str
    status: str
    risk_level: Optional[str] = None
    key_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonaSummary:
    """Aggregated summary for one persona's applications for a customer."""
    persona: str
    persona_label: str
    application_count: int
    latest_status: str
    risk_level: Optional[str] = None
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    applications: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskCorrelation:
    """Cross-persona risk correlation insight."""
    severity: str  # "info", "warning", "critical"
    title: str
    description: str
    personas_involved: List[str] = field(default_factory=list)


@dataclass
class Customer360View:
    """Complete customer 360 view with profile, journey, and insights."""
    profile: CustomerProfile
    journey_events: List[CustomerJourneyEvent] = field(default_factory=list)
    persona_summaries: List[PersonaSummary] = field(default_factory=list)
    risk_correlations: List[RiskCorrelation] = field(default_factory=list)
    total_products: int = 0
    active_claims: int = 0
    overall_risk: str = "low"


# =============================================================================
# Persona display labels
# =============================================================================

PERSONA_LABELS = {
    "underwriting": "Life & Health Underwriting",
    "life_health_claims": "Life & Health Claims",
    "automotive_claims": "Automotive Claims",
    "mortgage_underwriting": "Mortgage Underwriting",
    "mortgage": "Mortgage Underwriting",
}


# =============================================================================
# Storage Functions (supports local filesystem and Azure Blob)
# =============================================================================

def _customers_dir(storage_root: str) -> Path:
    return Path(storage_root) / "customers"


def _get_blob_container():
    """Get Azure Blob container client if provider is Azure, else None."""
    try:
        from app.storage_providers import get_storage_provider
        from app.storage_providers.azure_blob import AzureBlobStorageProvider
        provider = get_storage_provider()
        if isinstance(provider, AzureBlobStorageProvider):
            return provider._container_client
    except Exception:
        pass
    return None


def _load_blob_json(blob_path: str) -> Optional[Any]:
    """Load JSON from Azure Blob. Returns None if not found."""
    container = _get_blob_container()
    if not container:
        return None
    try:
        data = container.download_blob(blob_path).readall()
        return json.loads(data)
    except Exception as e:
        logger.debug("Blob read failed for %s: %s", blob_path, e)
        return None


def _list_blob_prefixes(prefix: str) -> List[str]:
    """List unique sub-prefixes under a blob prefix (simulates directory listing)."""
    container = _get_blob_container()
    if not container:
        return []
    try:
        names = set()
        for blob in container.list_blobs(name_starts_with=prefix):
            rest = blob.name[len(prefix):]
            parts = rest.split("/")
            if parts[0]:
                names.add(parts[0])
        return sorted(names)
    except Exception as e:
        logger.debug("Blob list failed for prefix %s: %s", prefix, e)
        return []


def save_customer_profile(storage_root: str, profile: CustomerProfile) -> None:
    """Save a customer profile to disk."""
    customer_dir = _customers_dir(storage_root) / profile.id
    customer_dir.mkdir(parents=True, exist_ok=True)
    profile_path = customer_dir / "profile.json"
    profile_path.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")
    logger.info("Saved customer profile: %s", profile.id)


def save_customer_journey(
    storage_root: str,
    customer_id: str,
    events: List[CustomerJourneyEvent],
) -> None:
    """Save pre-computed journey events for a customer."""
    customer_dir = _customers_dir(storage_root) / customer_id
    customer_dir.mkdir(parents=True, exist_ok=True)
    journey_path = customer_dir / "journey.json"
    journey_path.write_text(
        json.dumps([asdict(e) for e in events], indent=2), encoding="utf-8"
    )
    logger.info("Saved %d journey events for customer %s", len(events), customer_id)


def save_customer_risk_correlations(
    storage_root: str,
    customer_id: str,
    correlations: List[RiskCorrelation],
) -> None:
    """Save risk correlations for a customer."""
    customer_dir = _customers_dir(storage_root) / customer_id
    customer_dir.mkdir(parents=True, exist_ok=True)
    path = customer_dir / "risk_correlations.json"
    path.write_text(
        json.dumps([asdict(c) for c in correlations], indent=2), encoding="utf-8"
    )


def load_customer_profile(storage_root: str, customer_id: str) -> Optional[CustomerProfile]:
    """Load a customer profile (blob-first, local fallback)."""
    # Try Azure Blob
    blob_data = _load_blob_json(f"customers/{customer_id}/profile.json")
    if blob_data:
        return CustomerProfile(**blob_data)
    # Local fallback
    profile_path = _customers_dir(storage_root) / customer_id / "profile.json"
    if not profile_path.exists():
        return None
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    return CustomerProfile(**data)


def load_customer_journey(
    storage_root: str, customer_id: str
) -> List[CustomerJourneyEvent]:
    """Load pre-computed journey events (blob-first, local fallback)."""
    blob_data = _load_blob_json(f"customers/{customer_id}/journey.json")
    if blob_data and isinstance(blob_data, list):
        return [CustomerJourneyEvent(**e) for e in blob_data]
    path = _customers_dir(storage_root) / customer_id / "journey.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [CustomerJourneyEvent(**e) for e in data]


def load_customer_risk_correlations(
    storage_root: str, customer_id: str
) -> List[RiskCorrelation]:
    """Load risk correlations (blob-first, local fallback)."""
    blob_data = _load_blob_json(f"customers/{customer_id}/risk_correlations.json")
    if blob_data and isinstance(blob_data, list):
        return [RiskCorrelation(**c) for c in blob_data]
    path = _customers_dir(storage_root) / customer_id / "risk_correlations.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RiskCorrelation(**c) for c in data]


def list_customers(storage_root: str) -> List[CustomerProfile]:
    """List all customer profiles (blob-first, local fallback)."""
    # Try Azure Blob
    customer_ids = _list_blob_prefixes("customers/")
    if customer_ids:
        profiles: List[CustomerProfile] = []
        for cid in customer_ids:
            profile = load_customer_profile(storage_root, cid)
            if profile:
                profiles.append(profile)
        return profiles
    # Local fallback
    customers_dir = _customers_dir(storage_root)
    if not customers_dir.exists():
        return []
    profiles = []
    for customer_dir in sorted(customers_dir.iterdir()):
        if customer_dir.is_dir():
            profile = load_customer_profile(storage_root, customer_dir.name)
            if profile:
                profiles.append(profile)
    return profiles


def get_customer_360(storage_root: str, customer_id: str) -> Optional[Customer360View]:
    """Build the full Customer 360 view."""
    profile = load_customer_profile(storage_root, customer_id)
    if not profile:
        return None

    journey_events = load_customer_journey(storage_root, customer_id)
    risk_correlations = load_customer_risk_correlations(storage_root, customer_id)

    # Build persona summaries from journey events
    persona_apps: Dict[str, List[CustomerJourneyEvent]] = {}
    for event in journey_events:
        persona_apps.setdefault(event.persona, []).append(event)

    persona_summaries: List[PersonaSummary] = []
    active_claims = 0
    for persona, events in persona_apps.items():
        latest = max(events, key=lambda e: e.date)
        summary = PersonaSummary(
            persona=persona,
            persona_label=PERSONA_LABELS.get(persona, persona),
            application_count=len(set(e.application_id for e in events)),
            latest_status=latest.status,
            risk_level=latest.risk_level,
            key_metrics=latest.key_metrics,
            applications=[asdict(e) for e in events],
        )
        persona_summaries.append(summary)
        if persona in ("life_health_claims", "automotive_claims") and latest.status not in (
            "closed",
            "denied",
        ):
            active_claims += 1

    return Customer360View(
        profile=profile,
        journey_events=sorted(journey_events, key=lambda e: e.date, reverse=True),
        persona_summaries=persona_summaries,
        risk_correlations=risk_correlations,
        total_products=len(persona_summaries),
        active_claims=active_claims,
        overall_risk=profile.risk_tier,
    )


def delete_customer(storage_root: str, customer_id: str) -> bool:
    """Delete a customer profile and all associated data."""
    import shutil

    customer_dir = _customers_dir(storage_root) / customer_id
    if customer_dir.exists():
        shutil.rmtree(customer_dir)
        logger.info("Deleted customer: %s", customer_id)
        return True
    return False
