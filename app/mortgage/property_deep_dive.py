"""
Property Deep Dive Engine for Canadian Mortgage Underwriting.

Queries REALTOR.ca for comparable sales, price trends, and risk
classification to support auto-appraisal decisions.
Falls back to Bing web search when REALTOR.ca is unavailable.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_REALTOR_CA_SEARCH_URL = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.realtor.ca",
    "Referer": "https://www.realtor.ca/",
}
_RATE_LIMIT_SECONDS = 1.0
_last_request_time: float = 0.0

# Cached requests Session with REALTOR.ca cookies
_realtor_session: requests.Session | None = None


def _rate_limit() -> None:
    """Enforce a minimum interval between outbound HTTP requests."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _RATE_LIMIT_SECONDS:
        time.sleep(_RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.monotonic()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PropertyDeepDiveResult:
    """Complete property deep-dive analysis."""

    property_summary: dict[str, Any]
    risk_classification: str  # "low" | "medium" | "high"
    risk_rationale: str
    auto_appraisal_eligible: bool
    auto_appraisal_recommendation: str
    comparable_sales: list[dict[str, Any]]
    price_trend: dict[str, Any]
    property_features: list[dict[str, Any]]
    appraisal_data_points: dict[str, Any]
    mls_listing_url: Optional[str] = None
    mls_number: Optional[str] = None
    photos: list[dict[str, Any]] = field(default_factory=list)
    needs_physical_appraisal: bool = False
    physical_appraisal_reason: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "property_summary": self.property_summary,
            "risk_classification": self.risk_classification,
            "risk_rationale": self.risk_rationale,
            "auto_appraisal_eligible": self.auto_appraisal_eligible,
            "auto_appraisal_recommendation": self.auto_appraisal_recommendation,
            "comparable_sales": self.comparable_sales,
            "price_trend": self.price_trend,
            "property_features": self.property_features,
            "appraisal_data_points": self.appraisal_data_points,
            "mls_listing_url": self.mls_listing_url,
            "mls_number": self.mls_number,
            "photos": self.photos,
            "needs_physical_appraisal": self.needs_physical_appraisal,
            "physical_appraisal_reason": self.physical_appraisal_reason,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Helper: geocode an address to lat/lon via Nominatim
# ---------------------------------------------------------------------------

def _geocode_address(address: str) -> Optional[tuple[float, float]]:
    """Return (latitude, longitude) for *address* or ``None`` on failure."""
    try:
        _rate_limit()
        resp = requests.get(
            _NOMINATIM_URL,
            params={"q": address, "format": "json", "countrycodes": "ca", "limit": 1},
            headers=_REQUEST_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        logger.warning("Geocoding failed for '%s'", address, exc_info=True)
    return None


# ---------------------------------------------------------------------------
# Helper: query REALTOR.ca
# ---------------------------------------------------------------------------

def _get_realtor_session() -> requests.Session:
    """Return a requests Session pre-warmed with REALTOR.ca cookies."""
    global _realtor_session
    if _realtor_session is not None:
        return _realtor_session
    s = requests.Session()
    s.headers.update(_REQUEST_HEADERS)
    try:
        _rate_limit()
        # Visit the homepage to pick up cookies / CAPTCHA tokens
        s.get("https://www.realtor.ca/", timeout=10)
    except Exception:
        logger.debug("Failed to warm REALTOR.ca session", exc_info=True)
    _realtor_session = s
    return s


def _search_realtor_ca(
    lat: float,
    lon: float,
    *,
    transaction_type: int = 2,
    price_min: int = 0,
    price_max: int = 0,
    property_search_type: int = 1,
    records_per_page: int = 12,
) -> list[dict[str, Any]]:
    """Query the REALTOR.ca listing search endpoint.

    *transaction_type*: 1 = active listings, 2 = sold / comparable sales.
    Returns parsed listing dicts or an empty list on failure.
    """
    # Build a bounding box roughly ±5 km around the point
    delta_lat = 0.045  # ~5 km
    delta_lon = 0.065  # ~5 km at Canadian latitudes

    form_data = {
        "ZoomLevel": "11",
        "LatitudeMax": str(round(lat + delta_lat, 6)),
        "LatitudeMin": str(round(lat - delta_lat, 6)),
        "LongitudeMax": str(round(lon + delta_lon, 6)),
        "LongitudeMin": str(round(lon - delta_lon, 6)),
        "CurrentPage": "1",
        "RecordsPerPage": str(records_per_page),
        "PropertySearchTypeId": str(property_search_type),
        "TransactionTypeId": str(transaction_type),
        "CultureId": "1",
        "ApplicationId": "1",
        "Version": "7.0",
    }
    if price_min:
        form_data["PriceMin"] = str(price_min)
    if price_max:
        form_data["PriceMax"] = str(price_max)

    try:
        _rate_limit()
        session = _get_realtor_session()
        resp = session.post(
            _REALTOR_CA_SEARCH_URL,
            data=form_data,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("Results", [])
    except Exception:
        logger.warning("REALTOR.ca search failed", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_price(price_str: str | None) -> float:
    """Best-effort parse of price strings like '$625,000'."""
    if not price_str:
        return 0.0
    if isinstance(price_str, (int, float)):
        return float(price_str)
    cleaned = price_str.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _extract_listing_property(listing: dict[str, Any]) -> dict[str, Any]:
    """Normalise a REALTOR.ca listing into a flat dict."""
    prop = listing.get("Property", {})
    address = prop.get("Address", {})
    building = listing.get("Building", {}) or {}
    land = listing.get("Land", {}) or {}

    address_text = address.get("AddressText", "")
    price = _parse_price(prop.get("Price"))
    bedrooms = building.get("Bedrooms", "")
    bathrooms = building.get("BathroomTotal", "")
    living_area_raw = building.get("SizeInterior", "")

    # Parse living area – values like "1200 sqft"
    living_area = 0.0
    if living_area_raw:
        for part in str(living_area_raw).replace(",", "").split():
            try:
                living_area = float(part)
                break
            except ValueError:
                continue

    return {
        "address": address_text,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "living_area": living_area,
        "lot_size": land.get("SizeTotal", ""),
        "property_type": building.get("Type", ""),
        "year_built": prop.get("OwnershipType", ""),
        "mls_number": listing.get("MlsNumber", ""),
        "photos": [
            {
                "url": p.get("HighResPath") or p.get("MedResPath") or p.get("LowResPath", ""),
                "caption": p.get("Description", ""),
                "category": _classify_photo(p.get("Description", "")),
            }
            for p in (prop.get("Photo", []) or [])
        ],
        "posted_date": listing.get("PostedDate", ""),
        "price_change_date": prop.get("PriceChangeDateUTC", ""),
    }


def _classify_photo(caption: str) -> str:
    """Classify a photo caption into a category."""
    c = caption.lower()
    if any(w in c for w in ("exterior", "front", "back", "yard", "curb")):
        return "exterior"
    if any(w in c for w in ("aerial", "drone", "bird")):
        return "aerial"
    if any(w in c for w in ("floor plan", "floorplan", "layout")):
        return "floorplan"
    return "interior"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in km between two lat/lon points."""
    import math
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _similarity_score(
    subject_price: float,
    comp_price: float,
    subject_beds: int,
    comp_beds: Any,
    subject_area: float,
    comp_area: float,
    distance_km: float,
) -> float:
    """Return 0-100 similarity score between subject property and a comp."""
    score = 100.0

    # Price proximity (up to -30)
    if subject_price and comp_price:
        pct_diff = abs(comp_price - subject_price) / subject_price
        score -= min(pct_diff * 100, 30)

    # Bedroom match (up to -20)
    try:
        bed_diff = abs(int(comp_beds or 0) - int(subject_beds or 0))
    except (ValueError, TypeError):
        bed_diff = 2
    score -= min(bed_diff * 10, 20)

    # Living area proximity (up to -20)
    if subject_area and comp_area:
        area_diff = abs(comp_area - subject_area) / max(subject_area, 1)
        score -= min(area_diff * 50, 20)

    # Distance penalty (up to -30)
    score -= min(distance_km * 6, 30)

    return max(round(score, 1), 0)


# ---------------------------------------------------------------------------
# Bing Web Search fallback
# ---------------------------------------------------------------------------

_BING_SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
}

# Separate session for Bing (don't reuse REALTOR.ca session/cookies)
_bing_session: requests.Session | None = None


def _bing_search(query: str, count: int = 10) -> list[dict[str, str]]:
    """Scrape Bing search results (title, snippet, url) for *query*.

    No API key required — parses the public HTML results page.
    Returns a list of ``{"title", "snippet", "url"}`` dicts.
    """
    import base64
    global _bing_session

    try:
        time.sleep(1.0)  # Simple rate limit for Bing (separate from REALTOR.ca)
        if _bing_session is None:
            _bing_session = requests.Session()
            _bing_session.headers.update(_BING_SEARCH_HEADERS)
        resp = _bing_session.get(
            "https://www.bing.com/search",
            params={"q": query, "count": str(count)},
            timeout=15,
        )
        resp.raise_for_status()
        html = resp.text
    except Exception:
        logger.warning("Bing search failed for query: %s", query, exc_info=True)
        return []

    results: list[dict[str, str]] = []

    # Split on b_algo list items
    parts = re.split(r'<li\s[^>]*class="b_algo"[^>]*>', html)
    for block in parts[1:count + 1]:
        end = block.find("<li ")
        if end > 0:
            block = block[:end]

        # Extract URL — Bing uses redirect URLs with base64-encoded targets
        url = ""
        # Decode from bing.com/ck/a?...&u=a1<base64>...
        u_match = re.search(r'u=a1([A-Za-z0-9_-]+)', block)
        if u_match:
            try:
                encoded = u_match.group(1)
                # Pad base64 if needed
                padded = encoded + "=" * (4 - len(encoded) % 4)
                url = base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
            except Exception:
                pass

        # Fallback: use <cite> element
        if not url:
            cite_m = re.search(r'<cite[^>]*>(.*?)</cite>', block, re.DOTALL)
            if cite_m:
                cite_text = re.sub(r'<[^>]+>', '', cite_m.group(1)).strip()
                cite_text = cite_text.replace(" › ", "/").replace("›", "/")
                if not cite_text.startswith("http"):
                    cite_text = "https://" + cite_text
                url = cite_text

        # Title — find text inside the main anchor tag
        title = ""
        # Look for anchor with class "tilk" or within h2
        title_m = re.search(r'<a[^>]*>([^<]*(?:<strong>[^<]*</strong>[^<]*)*)</a>', block, re.DOTALL)
        if title_m:
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()

        # Snippet — Bing uses various containers
        snippet = ""
        for pattern in [
            r'<p\b[^>]*>(.*?)</p>',
            r'class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*algoSlug[^"]*"[^>]*>(.*?)</span>',
            r'class="[^"]*caption[^"]*"[^>]*>(.*?)</div>',
        ]:
            snip_m = re.search(pattern, block, re.DOTALL)
            if snip_m:
                snippet = re.sub(r'<[^>]+>', '', snip_m.group(1)).strip()
                if len(snippet) > 20:
                    break

        if url and (title or snippet):
            results.append({"title": title, "snippet": snippet, "url": url})
    return results


# ---------------------------------------------------------------------------
# Azure OpenAI Responses API with web_search_preview (Bing Grounding)
# ---------------------------------------------------------------------------

_RESPONSES_API_VERSION = "2025-04-01-preview"
_RESPONSES_API_MODEL = "gpt-4.1"


def _call_responses_api(prompt: str) -> str | None:
    """Call the Azure OpenAI Responses API with web_search_preview tool.

    Uses the AIServices endpoint (separate from the main Chat Completions
    endpoint) which supports the Responses API with built-in Bing Grounding.
    Returns the text output or None on failure.

    Requires env var AZURE_RESPONSES_API_ENDPOINT to be set.
    """
    import os
    endpoint = os.environ.get("AZURE_RESPONSES_API_ENDPOINT", "").rstrip("/")
    if not endpoint:
        return None

    try:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
    except Exception:
        logger.warning("Azure AD auth failed for Responses API", exc_info=True)
        return None

    url = f"{endpoint}/openai/responses"
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
    }
    body = {
        "model": _RESPONSES_API_MODEL,
        "tools": [{"type": "web_search_preview"}],
        "input": prompt,
    }

    try:
        _rate_limit()
        resp = requests.post(
            url,
            params={"api-version": _RESPONSES_API_VERSION},
            headers=headers,
            json=body,
            timeout=90,
        )
        resp.raise_for_status()
        result = resp.json()

        # Extract text from the Responses API output structure
        for item in result.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content.get("text", "")
        return None
    except Exception:
        logger.warning("Responses API call failed", exc_info=True)
        return None


def _search_property_via_llm(
    address: str, purchase_price: float, property_type: str
) -> dict[str, Any]:
    """Gather property market data using AI with live web grounding.

    Tries the Azure OpenAI Responses API (with Bing web search) first for
    live, cited data. Falls back to the standard Chat Completions API
    (LLM training knowledge) if the Responses API is unavailable.
    """
    data: dict[str, Any] = {
        "comps": [],
        "photos": [],
        "features": [],
        "listing_url": None,
        "area_avg_price": None,
        "area_name": None,
        "property_details": {},
    }

    json_prompt = f"""Research the following Canadian property and provide current market data.

Property: {address}
Purchase Price: ${purchase_price:,.0f} CAD
Property Type: {property_type}

Search for this property and similar recent sales in the same area. Provide a JSON response with:
{{
  "area_name": "neighbourhood/city name",
  "area_avg_price": current average home price for this area in CAD (number),
  "comparable_sales": [
    {{"address": "nearby address", "sold_price": price_in_cad, "bedrooms": N, "bathrooms": N, "living_area": sqft, "sold_date": "YYYY-MM"}}
  ],
  "property_details": {{
    "bedrooms": N, "bathrooms": N, "living_area": sqft, "lot_size": "size",
    "year_built": YYYY, "garages": N, "property_type_detail": "type"
  }},
  "features": [
    {{"category": "General|Rooms|Size|Exterior|Interior", "feature": "name", "value": "value"}}
  ],
  "market_trend": "up|down|stable",
  "yoy_change_pct": year-over-year price change percentage
}}

Include 3-5 comparable properties that have recently sold nearby. Use current market data.
Return ONLY valid JSON, no markdown or explanation."""

    content: str | None = None
    source = "unknown"

    # --- Strategy 1: Responses API with live Bing web search ---
    try:
        raw = _call_responses_api(
            f"You are a Canadian real estate market data analyst. "
            f"Return only valid JSON.\n\n{json_prompt}"
        )
        if raw:
            # Strip markdown fences / comments the model may still add
            cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned.strip())
            cleaned = re.sub(r'//[^\n]*', '', cleaned)
            if cleaned.startswith("{"):
                content = cleaned
                source = "Bing Web Search"
                logger.info("Responses API returned %d chars for %s", len(content), address)
    except Exception:
        logger.debug("Responses API path failed, trying chat_completion", exc_info=True)

    # --- Strategy 2: Chat Completions (LLM training knowledge) ---
    if content is None:
        try:
            from app.config import load_settings
            from app.openai_client import chat_completion

            settings = load_settings()
            result = chat_completion(
                settings.openai,
                messages=[
                    {"role": "system", "content": "You are a Canadian real estate market data analyst. Return only valid JSON."},
                    {"role": "user", "content": json_prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
                timeout=60,
            )
            raw = (
                result.get("choices", [{}])[0].get("message", {}).get("content", "")
                or result.get("content", "")
            )
            if raw:
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
                cleaned = re.sub(r'\s*```$', '', cleaned.strip())
                cleaned = re.sub(r'//[^\n]*', '', cleaned)
                content = cleaned
                source = "AI Market Analysis"
                logger.info("chat_completion returned %d chars for %s", len(content), address)
        except Exception:
            logger.warning("chat_completion path also failed for %s", address, exc_info=True)

    # --- Parse the JSON content ---
    if not content:
        logger.warning("No property data obtained for %s", address)
        return data

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse property JSON for %s: %s", address, content[:200])
        return data

    # Populate data from parsed response
    data["area_name"] = parsed.get("area_name")
    data["area_avg_price"] = parsed.get("area_avg_price")
    data["property_details"] = parsed.get("property_details", {})
    data["market_trend"] = parsed.get("market_trend", "stable")
    data["yoy_change_pct"] = parsed.get("yoy_change_pct")

    for comp in parsed.get("comparable_sales", []):
        price = comp.get("sold_price", 0)
        if isinstance(price, (int, float)) and price > 0:
            data["comps"].append({
                "address": comp.get("address", "Comparable"),
                "sold_price": float(price),
                "sold_date": comp.get("sold_date", ""),
                "distance_km": 0,
                "bedrooms": comp.get("bedrooms", 0),
                "bathrooms": comp.get("bathrooms", 0),
                "living_area": comp.get("living_area", 0),
                "price_psf": round(float(price) / max(comp.get("living_area", 1), 1), 2),
                "similarity_score": 60,
                "source": source,
            })

    for feat in parsed.get("features", []):
        data["features"].append({
            "category": feat.get("category", "General"),
            "feature": feat.get("feature", ""),
            "value": str(feat.get("value", "")),
            "data_point_source": source,
        })

    logger.info(
        "Property search via %s returned %d comps, %d features for %s",
        source, len(data["comps"]), len(data["features"]), address,
    )
    return data


def _extract_details_from_snippet(snippet: str, data: dict[str, Any]) -> None:
    """Parse property details from a search snippet into *data*."""
    details = data.setdefault("property_details", {})
    features = data.setdefault("features", [])

    def _add_feature(category: str, name: str, value: str) -> None:
        if value and not any(f["feature"] == name and f["value"] == value for f in features):
            features.append({
                "category": category,
                "feature": name,
                "value": value,
                "data_point_source": "Web Search",
            })

    # Bedrooms
    beds = re.search(r'(\d+)\s*(?:bed(?:room)?s?|bd|br)\b', snippet, re.I)
    if beds:
        details["bedrooms"] = int(beds.group(1))
        _add_feature("Rooms", "Bedrooms", beds.group(1))

    # Bathrooms
    baths = re.search(r'(\d+(?:\.\d)?)\s*(?:bath(?:room)?s?|ba)\b', snippet, re.I)
    if baths:
        details["bathrooms"] = float(baths.group(1))
        _add_feature("Rooms", "Bathrooms", baths.group(1))

    # Square footage
    sqft = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft|sqft|square\s*feet)', snippet, re.I)
    if sqft:
        details["living_area"] = float(sqft.group(1).replace(",", ""))
        _add_feature("Size", "Living Area (sqft)", sqft.group(1))

    # Lot size
    lot = re.search(r'(?:lot|land)\s*(?:size)?[:\s]*([\d,.]+)\s*(sqft|sq\.?\s*ft|acres?|hectares?)', snippet, re.I)
    if lot:
        details["lot_size"] = f"{lot.group(1)} {lot.group(2)}"
        _add_feature("Size", "Lot Size", f"{lot.group(1)} {lot.group(2)}")

    # Year built
    year = re.search(r'(?:built|year\s*built|constructed)[:\s]*(\d{4})', snippet, re.I)
    if year:
        yr = int(year.group(1))
        if 1800 <= yr <= datetime.now().year:
            details["year_built"] = yr
            _add_feature("General", "Year Built", str(yr))

    # Garages
    garage = re.search(r'(\d+)\s*(?:car\s+)?garage', snippet, re.I)
    if garage:
        details["garages"] = int(garage.group(1))
        _add_feature("Exterior", "Garages", garage.group(1))

    # Parking
    parking = re.search(r'(\d+)\s*parking', snippet, re.I)
    if parking:
        details["parking"] = parking.group(1)
        _add_feature("Exterior", "Parking Spaces", parking.group(1))

    # Property type
    ptype = re.search(r'\b(detached|semi-detached|townhouse|condo(?:minium)?|bungalow|duplex|triplex)\b', snippet, re.I)
    if ptype:
        details["property_type_web"] = ptype.group(1).title()
        _add_feature("General", "Property Type (Web)", ptype.group(1).title())


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PropertyDeepDiveEngine:
    """Analyse a property using REALTOR.ca data for underwriting."""

    def __init__(
        self,
        property_address: str,
        purchase_price: float,
        property_type: str = "single_family_detached",
        appraised_value: float = 0.0,
        year_built: int | None = None,
        bedrooms: int | None = None,
        bathrooms: int | None = None,
        living_area: float | None = None,
        lot_size: str | None = None,
    ) -> None:
        self.property_address = property_address
        self.purchase_price = purchase_price
        self.property_type = property_type.lower() if property_type else "single_family_detached"
        self.appraised_value = appraised_value or purchase_price
        self.year_built = year_built
        self.bedrooms = bedrooms or 0
        self.bathrooms = bathrooms or 0
        self.living_area = living_area or 0.0
        self.lot_size = lot_size
        self._warnings: list[str] = []
        self._lat: float | None = None
        self._lon: float | None = None

    # ----- public API -------------------------------------------------------

    def analyze(self) -> PropertyDeepDiveResult:
        """Run the full property deep-dive analysis."""
        # 1. Geocode
        coords = _geocode_address(self.property_address)
        if coords:
            self._lat, self._lon = coords
        else:
            self._warnings.append("Geocoding failed – comparable search skipped.")

        # 2. Look up the subject property on REALTOR.ca
        subject_listing = self._find_subject_listing()

        # 3. Fetch comparable sales
        comps = self._fetch_comparables()

        # 4. If MLS data is empty, fall back to Bing web search
        web_data: dict[str, Any] = {}
        if not comps and not subject_listing:
            logger.info("MLS data unavailable — falling back to AI market analysis")
            web_data = _search_property_via_llm(
                self.property_address, self.purchase_price, self.property_type
            )
            comps = web_data.get("comps", [])
            if comps:
                self._warnings.append(
                    f"MLS unavailable; AI market analysis provided {len(comps)} comps."
                )
            else:
                self._warnings.append("MLS unavailable; AI market analysis found no comparables.")

        # 5. Price trends
        price_trend = self._compute_price_trend(comps)
        # Enrich from web search if area average found
        if web_data.get("area_avg_price"):
            price_trend["avg_price_current"] = web_data["area_avg_price"]
            if web_data.get("area_name"):
                price_trend["area_name"] = web_data["area_name"]

        # 6. Risk classification
        risk, rationale = self._classify_risk(comps, price_trend)

        # 7. Auto-appraisal eligibility
        eligible, recommendation, needs_phys, phys_reason = self._assess_auto_appraisal(
            risk, comps
        )

        # 8. Property features & data points from listing
        features, data_points = self._extract_features(subject_listing)
        # Merge web search features
        if web_data.get("features"):
            for wf in web_data["features"]:
                if not any(f["feature"] == wf["feature"] for f in features):
                    features.append(wf)

        # Enrich from web details
        web_details = web_data.get("property_details", {})
        if web_details:
            for key in ("bedrooms", "bathrooms", "living_area", "lot_size",
                        "year_built", "garages", "parking"):
                if web_details.get(key) and not getattr(self, key, None):
                    setattr(self, key, web_details[key])

        # 9. Photos — merge web and MLS
        photos = self._extract_photos(subject_listing)
        if web_data.get("photos"):
            photos.extend(web_data["photos"])

        summary = {
            "address": self.property_address,
            "type": self.property_type,
            "purchase_price": self.purchase_price,
            "appraised_value": self.appraised_value,
            "year_built": self.year_built or web_details.get("year_built"),
            "lot_size": self.lot_size or web_details.get("lot_size"),
            "living_area": self.living_area or web_details.get("living_area", 0),
            "bedrooms": self.bedrooms or web_details.get("bedrooms", 0),
            "bathrooms": self.bathrooms or web_details.get("bathrooms", 0),
            "garages": (subject_listing.get("garages") if subject_listing else None)
                       or web_details.get("garages"),
            "parking": (subject_listing.get("parking") if subject_listing else None)
                       or web_details.get("parking"),
        }

        listing_url = (
            (subject_listing.get("mls_listing_url") if subject_listing else None)
            or web_data.get("listing_url")
        )
        mls_number = subject_listing.get("mls_number") if subject_listing else None

        return PropertyDeepDiveResult(
            property_summary=summary,
            risk_classification=risk,
            risk_rationale=rationale,
            auto_appraisal_eligible=eligible,
            auto_appraisal_recommendation=recommendation,
            comparable_sales=comps,
            price_trend=price_trend,
            property_features=features,
            appraisal_data_points=data_points,
            mls_listing_url=listing_url,
            mls_number=mls_number,
            photos=photos,
            needs_physical_appraisal=needs_phys,
            physical_appraisal_reason=phys_reason,
            warnings=list(self._warnings),
        )

    # ----- internals --------------------------------------------------------

    def _find_subject_listing(self) -> dict[str, Any] | None:
        """Try to find the subject property on REALTOR.ca."""
        if self._lat is None or self._lon is None:
            return None

        # Search active listings near the exact coordinates with a tight bbox
        results = _search_realtor_ca(
            self._lat,
            self._lon,
            transaction_type=1,
            records_per_page=20,
        )

        # Match on address substring
        addr_lower = self.property_address.lower()
        addr_tokens = [t for t in addr_lower.replace(",", " ").split() if len(t) > 2]

        best: dict[str, Any] | None = None
        best_score = 0

        for listing in results:
            parsed = _extract_listing_property(listing)
            listing_addr = parsed.get("address", "").lower()
            match_count = sum(1 for t in addr_tokens if t in listing_addr)
            if match_count > best_score:
                best_score = match_count
                best = parsed
                best["mls_listing_url"] = (
                    f"https://www.realtor.ca/real-estate/{parsed.get('mls_number', '')}"
                )

        if best and best_score >= max(len(addr_tokens) // 2, 2):
            return best

        self._warnings.append("Subject property not found on REALTOR.ca active listings.")
        return None

    def _fetch_comparables(self) -> list[dict[str, Any]]:
        """Fetch recently sold comparable properties."""
        if self._lat is None or self._lon is None:
            return []

        # Search for sold properties (TransactionTypeId=2) within price range
        margin = 0.35
        price_min = int(self.purchase_price * (1 - margin)) if self.purchase_price else 0
        price_max = int(self.purchase_price * (1 + margin)) if self.purchase_price else 0

        results = _search_realtor_ca(
            self._lat,
            self._lon,
            transaction_type=2,
            price_min=price_min,
            price_max=price_max,
            records_per_page=20,
        )

        comps: list[dict[str, Any]] = []
        for listing in results:
            parsed = _extract_listing_property(listing)
            comp_price = parsed.get("price", 0)
            if not comp_price:
                continue

            # Geocode comp for distance (approximate from listing address)
            comp_coords = _geocode_address(parsed["address"])
            distance_km = 0.0
            if comp_coords and self._lat is not None:
                distance_km = _haversine_km(self._lat, self._lon, comp_coords[0], comp_coords[1])

            living_area = parsed.get("living_area", 0)
            psf = round(comp_price / living_area, 2) if living_area else 0.0

            sim = _similarity_score(
                self.purchase_price,
                comp_price,
                self.bedrooms,
                parsed.get("bedrooms"),
                self.living_area,
                living_area,
                distance_km,
            )

            comps.append({
                "address": parsed["address"],
                "sold_price": comp_price,
                "sold_date": parsed.get("posted_date", ""),
                "distance_km": round(distance_km, 2),
                "bedrooms": parsed.get("bedrooms", ""),
                "bathrooms": parsed.get("bathrooms", ""),
                "living_area": living_area,
                "price_psf": psf,
                "similarity_score": sim,
            })

        # Sort by similarity descending, keep top 10
        comps.sort(key=lambda c: c["similarity_score"], reverse=True)
        return comps[:10]

    def _compute_price_trend(self, comps: list[dict[str, Any]]) -> dict[str, Any]:
        """Derive area price-trend metrics from comparables."""
        if not comps:
            self._warnings.append("No comparable data – price trend unavailable.")
            return {
                "area_name": self.property_address,
                "avg_price_current": self.purchase_price,
                "avg_price_1yr_ago": None,
                "avg_price_3yr_ago": None,
                "yoy_change_pct": None,
                "cagr_3yr_pct": None,
                "trend_direction": "stable",
            }

        prices = [c["sold_price"] for c in comps if c.get("sold_price")]
        avg_current = sum(prices) / len(prices) if prices else self.purchase_price

        # Without historical snapshots we estimate from the spread
        avg_1yr = round(avg_current * 0.95, 2)   # conservative 5 % appreciation assumption
        avg_3yr = round(avg_current * 0.85, 2)

        yoy = round((avg_current - avg_1yr) / avg_1yr * 100, 2) if avg_1yr else 0
        cagr = None
        if avg_3yr and avg_3yr > 0:
            cagr = round(((avg_current / avg_3yr) ** (1 / 3) - 1) * 100, 2)

        direction = "stable"
        if yoy and yoy > 5:
            direction = "up"
        elif yoy and yoy < -5:
            direction = "down"

        return {
            "area_name": self.property_address,
            "avg_price_current": round(avg_current, 2),
            "avg_price_1yr_ago": avg_1yr,
            "avg_price_3yr_ago": avg_3yr,
            "yoy_change_pct": yoy,
            "cagr_3yr_pct": cagr,
            "trend_direction": direction,
        }

    def _classify_risk(
        self, comps: list[dict[str, Any]], price_trend: dict[str, Any]
    ) -> tuple[str, str]:
        """Return (risk_level, rationale)."""
        reasons: list[str] = []

        # --- HIGH risk triggers ---
        # Manufactured / mobile home
        if self.property_type in ("mobile_home", "manufactured", "modular_home"):
            reasons.append("Manufactured/mobile home type carries higher risk.")
            return "high", "; ".join(reasons)

        comp_prices = [c["sold_price"] for c in comps if c.get("sold_price")]

        if len(comps) < 2:
            reasons.append("Very few or no comparable sales available.")
            return "high", "; ".join(reasons)

        avg_comp = sum(comp_prices) / len(comp_prices) if comp_prices else 0
        if avg_comp:
            price_premium = (self.purchase_price - avg_comp) / avg_comp * 100
        else:
            price_premium = 0

        if price_premium > 20:
            reasons.append(
                f"Purchase price is {price_premium:.0f}% above comparable average."
            )
            return "high", "; ".join(reasons)

        yoy = price_trend.get("yoy_change_pct") or 0
        if yoy > 20:
            reasons.append(f"Rapid area appreciation ({yoy:.1f}% YoY).")
            return "high", "; ".join(reasons)

        # --- MEDIUM risk triggers ---
        if 10 < price_premium <= 20:
            reasons.append(
                f"Purchase price is {price_premium:.0f}% above comparable average."
            )
        if self.property_type in ("mixed_use", "duplex", "triplex", "fourplex"):
            reasons.append("Rural or unique property type.")
        if 2 <= len(comps) < 4:
            reasons.append("Limited comparable data available.")
        if reasons:
            return "medium", "; ".join(reasons)

        # --- LOW risk ---
        low_reasons = []
        if self.property_type in ("condominium", "townhouse"):
            low_reasons.append("Condo/townhouse with high transaction volume.")
        if avg_comp and abs(price_premium) <= 10:
            low_reasons.append("Purchase price aligns with comparable average.")
        if len(comps) >= 5:
            low_reasons.append("Strong comparable data.")
        return "low", "; ".join(low_reasons) if low_reasons else "Property meets standard criteria."

    def _assess_auto_appraisal(
        self,
        risk: str,
        comps: list[dict[str, Any]],
    ) -> tuple[bool, str, bool, Optional[str]]:
        """Return (eligible, recommendation, needs_physical, physical_reason)."""
        close_comps = [c for c in comps if c.get("distance_km", 999) <= 5]

        if risk == "low" and len(close_comps) >= 3:
            return (
                True,
                "Auto-appraisal supported. Property aligns with area comparables.",
                False,
                None,
            )

        # Build reason for physical appraisal
        phys_reasons: list[str] = []
        if risk == "high":
            phys_reasons.append("Property classified as high risk.")
        if len(close_comps) < 3:
            phys_reasons.append(
                f"Insufficient nearby comparables ({len(close_comps)} within 5 km; 3 required)."
            )
        if risk == "medium" and not phys_reasons:
            phys_reasons.append("Medium risk classification requires manual review.")

        reason = " ".join(phys_reasons) if phys_reasons else "Insufficient data for auto-appraisal."
        return (
            False,
            f"Physical appraisal required. {reason}",
            True,
            reason,
        )

    def _extract_features(
        self, listing: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Extract property features and appraisal data points."""
        features: list[dict[str, Any]] = []
        data_points: dict[str, Any] = {}

        def _add(category: str, feature: str, value: Any, source: str = "MLS Listing") -> None:
            if value:
                features.append({
                    "category": category,
                    "feature": feature,
                    "value": value,
                    "data_point_source": source,
                })

        _add("General", "Property Type", self.property_type, "Application")
        _add("General", "Year Built", self.year_built, "Application")
        _add("Size", "Living Area", self.living_area, "Application")
        _add("Size", "Lot Size", self.lot_size, "Application")
        _add("Rooms", "Bedrooms", self.bedrooms, "Application")
        _add("Rooms", "Bathrooms", self.bathrooms, "Application")

        if listing:
            _add("General", "MLS Property Type", listing.get("property_type"))
            _add("Size", "MLS Living Area", listing.get("living_area"))
            _add("Size", "MLS Lot Size", listing.get("lot_size"))

            data_points = {
                "lot_dimensions": listing.get("lot_size"),
                "zoning": None,
                "basement": None,
                "heating": None,
                "cooling": None,
                "water_supply": None,
                "sewage": None,
                "exterior_finish": None,
                "roof": None,
                "foundation": None,
            }
        else:
            data_points = {
                "lot_dimensions": self.lot_size,
                "zoning": None,
                "basement": None,
                "heating": None,
                "cooling": None,
                "water_supply": None,
                "sewage": None,
                "exterior_finish": None,
                "roof": None,
                "foundation": None,
            }

        return features, data_points

    def _extract_photos(self, listing: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Return photo metadata from the listing."""
        if listing and listing.get("photos"):
            return listing["photos"]
        return []
