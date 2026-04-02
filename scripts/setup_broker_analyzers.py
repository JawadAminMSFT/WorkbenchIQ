#!/usr/bin/env python3
"""
Setup script for Commercial Brokerage Custom Analyzers.

Creates and deploys custom Azure Content Understanding analyzers for:
- brokerQuoteAnalyzer: Extract fields from carrier insurance quote documents
- brokerAcordAnalyzer: Extract ACORD 125/140 fields from submission documents
- brokerResearchAnalyzer: Extract carrier financial data from AM Best / research docs

Usage:
    python scripts/setup_broker_analyzers.py [--verify] [--delete]

Options:
    --verify    Only verify analyzers exist, don't create/update
    --delete    Delete all broker analyzers
    --force     Force recreate even if analyzers exist
    --json      Output analyzer schemas as JSON
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.broker.cu_schemas import (
    BROKER_ACORD_FIELD_SCHEMA,
    BROKER_QUOTE_FIELD_SCHEMA,
    BROKER_RESEARCH_FIELD_SCHEMA,
)

# =============================================================================
# Analyzer Configurations
# =============================================================================

ANALYZER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "brokerQuoteAnalyzer": {
        "description": "Commercial brokerage analyzer for carrier insurance quote documents",
        "baseAnalyzerId": "prebuilt-document",
        "fieldSchema": BROKER_QUOTE_FIELD_SCHEMA,
        "config": {
            "returnDetails": True,
            "enableOcr": True,
            "enableLayout": True,
            "tableFormat": "markdown",
            "estimateFieldSourceAndConfidence": True,
        },
        "models": {
            "completion": "gpt-4.1",
        },
    },
    "brokerAcordAnalyzer": {
        "description": "Commercial brokerage analyzer for ACORD 125/140 submission documents (SOV, loss runs, prior declarations)",
        "baseAnalyzerId": "prebuilt-document",
        "fieldSchema": BROKER_ACORD_FIELD_SCHEMA,
        "config": {
            "returnDetails": True,
            "enableOcr": True,
            "enableLayout": True,
            "tableFormat": "markdown",
            "estimateFieldSourceAndConfidence": True,
        },
        "models": {
            "completion": "gpt-4.1",
        },
    },
    "brokerResearchAnalyzer": {
        "description": "Commercial brokerage analyzer for AM Best credit reports and carrier financial research",
        "baseAnalyzerId": "prebuilt-document",
        "fieldSchema": BROKER_RESEARCH_FIELD_SCHEMA,
        "config": {
            "returnDetails": True,
            "enableOcr": True,
            "enableLayout": True,
            "tableFormat": "markdown",
            "estimateFieldSourceAndConfidence": True,
        },
        "models": {
            "completion": "gpt-4.1",
        },
    },
}


# =============================================================================
# Azure Content Understanding API Functions
# =============================================================================

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for Azure CU API."""
    use_azure_ad = os.getenv("AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD", "true").lower() == "true"
    api_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY")

    headers = {"x-ms-useragent": "broker-cu-setup"}

    if use_azure_ad:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
        except ImportError:
            raise RuntimeError("azure-identity not installed. Run: uv add azure-identity")
        except Exception as e:
            raise RuntimeError(f"Failed to get Azure AD token: {e}. Run: az login")
    elif api_key:
        headers["Ocp-Apim-Subscription-Key"] = api_key
    else:
        raise RuntimeError("No authentication configured. Set AZURE_CONTENT_UNDERSTANDING_API_KEY or use Azure AD.")

    return headers


def get_analyzer(analyzer_id: str) -> Optional[Dict[str, Any]]:
    """Check if an analyzer exists and get its configuration."""
    import requests

    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")

    if not endpoint:
        raise RuntimeError("AZURE_CONTENT_UNDERSTANDING_ENDPOINT not set")

    headers = get_auth_headers()
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if "404" in str(e):
            return None
        raise


def poll_operation(response, headers: Dict[str, str], timeout: int = 120) -> Dict[str, Any]:
    """Poll an async operation until completion."""
    import requests

    operation_url = response.headers.get("Operation-Location")
    if not operation_url:
        return {"status": "succeeded"}

    start_time = time.time()
    while time.time() - start_time < timeout:
        result = requests.get(operation_url, headers=headers, timeout=30)
        result.raise_for_status()
        data = result.json()

        status = data.get("status", "").lower()
        if status == "succeeded":
            return data.get("result", data)
        elif status == "failed":
            raise RuntimeError(f"Operation failed: {data.get('error', 'Unknown error')}")

        time.sleep(2)

    raise RuntimeError(f"Operation timed out after {timeout} seconds")


def create_analyzer(analyzer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new custom analyzer."""
    import requests

    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")

    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"

    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}

    body = {
        "analyzerId": analyzer_id,
        **config,
    }

    response = requests.put(url, headers=headers, params=params, json=body, timeout=60)
    response.raise_for_status()

    if response.status_code == 202:
        return poll_operation(response, headers)

    return response.json() if response.text else {"analyzerId": analyzer_id, "status": "succeeded"}


def update_analyzer(analyzer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing analyzer (delete and recreate)."""
    delete_analyzer(analyzer_id)
    time.sleep(2)
    return create_analyzer(analyzer_id, config)


def delete_analyzer(analyzer_id: str) -> bool:
    """Delete an analyzer."""
    import requests

    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")

    headers = get_auth_headers()
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}

    response = requests.delete(url, headers=headers, params=params, timeout=30)
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


def verify_analyzer(analyzer_id: str) -> bool:
    """Verify an analyzer exists and is ready."""
    analyzer = get_analyzer(analyzer_id)
    if analyzer:
        print(f"  ✓ {analyzer_id}: Ready")
        print(f"    Base: {analyzer.get('baseAnalyzerId', 'unknown')}")
        fields = analyzer.get("fieldSchema", {}).get("fields", {})
        print(f"    Fields: {len(fields)} defined")
        return True
    else:
        print(f"  ✗ {analyzer_id}: Not found")
        return False


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Setup commercial brokerage custom analyzers in Azure Content Understanding"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify analyzers exist, don't create/update",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete all broker analyzers",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate even if analyzers exist",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output analyzer schemas as JSON",
    )

    args = parser.parse_args()

    # Output JSON schema if requested
    if args.json:
        print(json.dumps(ANALYZER_CONFIGS, indent=2))
        return

    print("\n" + "=" * 60)
    print("  Commercial Brokerage Analyzer Setup")
    print("  Analyzers: quote, acord, research")
    print("=" * 60 + "\n")

    # Verify mode
    if args.verify:
        print("Verifying broker analyzers...\n")
        all_ok = True
        for analyzer_id in ANALYZER_CONFIGS:
            if not verify_analyzer(analyzer_id):
                all_ok = False
        sys.exit(0 if all_ok else 1)

    # Delete mode
    if args.delete:
        print("Deleting broker analyzers...\n")
        for analyzer_id in ANALYZER_CONFIGS:
            if delete_analyzer(analyzer_id):
                print(f"  ✓ {analyzer_id} deleted")
            else:
                print(f"  - {analyzer_id} not found (already deleted)")
        return

    # Create/Update mode
    print("Setting up broker document analyzers...\n")

    for analyzer_id, config in ANALYZER_CONFIGS.items():
        existing = get_analyzer(analyzer_id)

        if existing and not args.force:
            print(f"  ℹ {analyzer_id} already exists")
            print(f"    Use --force to recreate")
            verify_analyzer(analyzer_id)
        else:
            if existing:
                print(f"  Updating {analyzer_id}...")
                result = update_analyzer(analyzer_id, config)
            else:
                print(f"  Creating {analyzer_id}...")
                result = create_analyzer(analyzer_id, config)

            print(f"  ✓ {analyzer_id} ready")
            print(f"    Fields: {len(config['fieldSchema']['fields'])}")

        print()

    print("=" * 60)
    print("  Setup complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
