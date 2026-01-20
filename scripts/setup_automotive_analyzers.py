#!/usr/bin/env python3
"""
Setup script for Automotive Claims Custom Analyzers.

Creates and deploys custom Azure Content Understanding analyzers for:
- autoClaimsDocAnalyzer: Document extraction for claims, estimates, police reports
- autoClaimsImageAnalyzer: Damage detection from vehicle photos
- autoClaimsVideoAnalyzer: Incident analysis from dashcam/surveillance video

Usage:
    python scripts/setup_automotive_analyzers.py [--verify] [--delete]
    
Options:
    --verify    Only verify analyzers exist, don't create/update
    --delete    Delete all automotive claims analyzers
    --force     Force recreate even if analyzers exist
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

# =============================================================================
# Analyzer Schema Definitions
# =============================================================================

# Document Analyzer Schema - for claims forms, repair estimates, police reports
AUTO_CLAIMS_DOC_ANALYZER_SCHEMA = {
    "name": "AutoClaimsDocFields",
    "description": "Field schema for automotive claims document extraction",
    "fields": {
        # Claim Identification
        "ClaimNumber": {
            "type": "string",
            "method": "extract",
            "description": "Unique claim reference number",
        },
        "PolicyNumber": {
            "type": "string",
            "method": "extract",
            "description": "Insurance policy number",
        },
        "DateOfLoss": {
            "type": "date",
            "method": "extract",
            "description": "Date the incident occurred",
        },
        "DateReported": {
            "type": "date",
            "method": "extract",
            "description": "Date the claim was reported",
        },
        
        # Vehicle Information
        "VehicleVIN": {
            "type": "string",
            "method": "extract",
            "description": "Vehicle Identification Number (17 characters)",
        },
        "VehicleMake": {
            "type": "string",
            "method": "extract",
            "description": "Vehicle manufacturer (Ford, Toyota, etc.)",
        },
        "VehicleModel": {
            "type": "string",
            "method": "extract",
            "description": "Vehicle model name",
        },
        "VehicleYear": {
            "type": "integer",
            "method": "extract",
            "description": "Vehicle model year",
        },
        "VehicleColor": {
            "type": "string",
            "method": "extract",
            "description": "Vehicle exterior color",
        },
        "VehicleMileage": {
            "type": "integer",
            "method": "extract",
            "description": "Odometer reading at time of loss",
        },
        
        # Incident Details
        "IncidentLocation": {
            "type": "string",
            "method": "extract",
            "description": "Address or location where incident occurred",
        },
        "IncidentDescription": {
            "type": "string",
            "method": "extract",
            "description": "Narrative description of the incident",
        },
        "WeatherConditions": {
            "type": "string",
            "method": "extract",
            "description": "Weather at time of incident (Clear, Rain, Snow, etc.)",
        },
        "RoadConditions": {
            "type": "string",
            "method": "extract",
            "description": "Road conditions (Dry, Wet, Icy, etc.)",
        },
        "PoliceReportNumber": {
            "type": "string",
            "method": "extract",
            "description": "Police report or case number if applicable",
        },
        
        # Parties Involved
        "Claimant": {
            "type": "object",
            "method": "extract",
            "description": "Person filing the claim",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "address": {"type": "string"},
                "driversLicense": {"type": "string"},
            },
        },
        "OtherParties": {
            "type": "array",
            "method": "extract",
            "description": "Other parties involved in the incident",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "insuranceCompany": {"type": "string"},
                    "policyNumber": {"type": "string"},
                    "vehicleInfo": {"type": "string"},
                },
            },
        },
        "Witnesses": {
            "type": "array",
            "method": "extract",
            "description": "Witnesses to the incident",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "statement": {"type": "string"},
                },
            },
        },
        
        # Repair Estimate Details
        "EstimateTotal": {
            "type": "number",
            "method": "extract",
            "description": "Total repair estimate amount in dollars",
        },
        "LaborCost": {
            "type": "number",
            "method": "extract",
            "description": "Labor charges for repairs",
        },
        "PartsCost": {
            "type": "number",
            "method": "extract",
            "description": "Cost of replacement parts",
        },
        "RepairShop": {
            "type": "object",
            "method": "extract",
            "description": "Repair facility information",
            "properties": {
                "name": {"type": "string"},
                "address": {"type": "string"},
                "phone": {"type": "string"},
                "estimateDate": {"type": "date"},
            },
        },
        "RepairLineItems": {
            "type": "array",
            "method": "extract",
            "description": "Individual repair line items",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "partNumber": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unitPrice": {"type": "number"},
                    "laborHours": {"type": "number"},
                    "totalPrice": {"type": "number"},
                },
            },
        },
        
        # Coverage Information
        "CoverageType": {
            "type": "string",
            "method": "extract",
            "description": "Type of coverage: Collision, Comprehensive, Liability, etc.",
        },
        "Deductible": {
            "type": "number",
            "method": "extract",
            "description": "Deductible amount",
        },
    },
}

# Image Analyzer Schema - for damage photos
AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA = {
    "name": "AutoClaimsImageFields",
    "description": "Field schema for automotive damage image analysis",
    "fields": {
        # Vehicle Identification from Image
        "VehicleIdentified": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether a vehicle is clearly visible in the image",
        },
        "VehicleType": {
            "type": "string",
            "method": "generate",
            "description": "Type of vehicle: Sedan, SUV, Truck, Van, Motorcycle, etc.",
        },
        "VehicleColor": {
            "type": "string",
            "method": "generate",
            "description": "Visible vehicle color",
        },
        "LicensePlateVisible": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether license plate is visible",
        },
        "LicensePlateNumber": {
            "type": "string",
            "method": "generate",
            "description": "License plate number if readable",
        },
        
        # Damage Assessment
        "DamageDetected": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether damage is visible in the image",
        },
        "DamageAreas": {
            "type": "array",
            "method": "generate",
            "description": "List of damaged areas detected",
            "items": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location: Front, Rear, Driver Side, Passenger Side, Hood, Roof, etc.",
                    },
                    "damageType": {
                        "type": "string",
                        "description": "Type: Dent, Scratch, Crack, Crush, Shatter, etc.",
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity: Minor, Moderate, Severe",
                    },
                    "components": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Affected components: Bumper, Door, Fender, Window, Mirror, etc.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the damage",
                    },
                },
            },
        },
        "OverallDamageSeverity": {
            "type": "string",
            "method": "generate",
            "description": "Overall severity assessment: Minor, Moderate, Heavy, Total Loss",
        },
        "EstimatedRepairCategory": {
            "type": "string",
            "method": "generate",
            "description": "Repair category: Cosmetic, Structural, Mechanical, Total Loss",
        },
        
        # Image Quality
        "ImageQuality": {
            "type": "string",
            "method": "generate",
            "description": "Image quality for assessment: Good, Fair, Poor",
        },
        "LightingConditions": {
            "type": "string",
            "method": "generate",
            "description": "Lighting: Daylight, Indoor, Low Light, Flash",
        },
        "AngleCoverage": {
            "type": "string",
            "method": "generate",
            "description": "Camera angle: Front, Side, Rear, Close-up, Wide",
        },
        
        # Context
        "EnvironmentVisible": {
            "type": "string",
            "method": "generate",
            "description": "Visible environment: Parking Lot, Street, Highway, Garage, etc.",
        },
        "OtherVehiclesVisible": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether other vehicles are visible in the image",
        },
    },
}

# Video Analyzer Schema - for dashcam/surveillance footage
AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA = {
    "name": "AutoClaimsVideoFields",
    "description": "Field schema for automotive incident video analysis",
    "fields": {
        # Video Metadata
        "VideoDuration": {
            "type": "string",
            "method": "extract",
            "description": "Total video duration",
        },
        "VideoSource": {
            "type": "string",
            "method": "generate",
            "description": "Source type: Dashcam, Surveillance, Phone, Body Camera",
        },
        "VideoQuality": {
            "type": "string",
            "method": "generate",
            "description": "Video quality: HD, SD, Low",
        },
        
        # Incident Detection
        "IncidentDetected": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether a collision/incident is visible in the video",
        },
        "ImpactTimestamp": {
            "type": "string",
            "method": "generate",
            "description": "Timestamp of primary impact if detected",
        },
        "IncidentType": {
            "type": "string",
            "method": "generate",
            "description": "Type: Rear-end, T-bone, Sideswipe, Head-on, Single Vehicle, Hit and Run",
        },
        
        # Video Segments
        "VideoSegments": {
            "type": "array",
            "method": "generate",
            "description": "Logical segments of the video",
            "items": {
                "type": "object",
                "properties": {
                    "startTime": {"type": "string"},
                    "endTime": {"type": "string"},
                    "label": {
                        "type": "string",
                        "description": "Segment label: Pre-Incident, Impact, Post-Incident",
                    },
                    "description": {"type": "string"},
                },
            },
        },
        
        # Vehicles in Video
        "VehiclesIdentified": {
            "type": "array",
            "method": "generate",
            "description": "Vehicles visible in the video",
            "items": {
                "type": "object",
                "properties": {
                    "vehicleId": {"type": "string"},
                    "type": {"type": "string"},
                    "color": {"type": "string"},
                    "role": {
                        "type": "string",
                        "description": "Role: Subject Vehicle, Other Party, Witness, Parked",
                    },
                    "licensePlate": {"type": "string"},
                },
            },
        },
        
        # Speed and Movement
        "EstimatedSpeed": {
            "type": "string",
            "method": "generate",
            "description": "Estimated speed at impact if determinable",
        },
        "MovementPattern": {
            "type": "string",
            "method": "generate",
            "description": "Movement: Straight, Turning, Lane Change, Reversing, Stopped",
        },
        
        # Audio/Transcript
        "Transcript": {
            "type": "string",
            "method": "extract",
            "description": "Transcript of any speech in the video",
        },
        "SignificantSounds": {
            "type": "array",
            "method": "generate",
            "description": "Notable sounds detected",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "soundType": {
                        "type": "string",
                        "description": "Type: Impact, Braking, Horn, Glass Breaking, etc.",
                    },
                },
            },
        },
        
        # Traffic/Environment
        "TrafficConditions": {
            "type": "string",
            "method": "generate",
            "description": "Traffic: Light, Moderate, Heavy, Stopped",
        },
        "WeatherVisible": {
            "type": "string",
            "method": "generate",
            "description": "Visible weather: Clear, Rain, Snow, Fog",
        },
        "TimeOfDay": {
            "type": "string",
            "method": "generate",
            "description": "Time of day: Daytime, Dusk, Dawn, Night",
        },
        
        # Liability Indicators
        "TrafficSignalsVisible": {
            "type": "array",
            "method": "generate",
            "description": "Traffic signals/signs visible",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "state": {"type": "string"},
                    "timestamp": {"type": "string"},
                },
            },
        },
        "LaneMarkingsVisible": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether lane markings are visible",
        },
        "RightOfWayViolation": {
            "type": "boolean",
            "method": "generate",
            "description": "Whether a right-of-way violation is apparent",
        },
    },
}


# =============================================================================
# Analyzer Configuration
# =============================================================================

def get_analyzer_configs() -> Dict[str, Dict[str, Any]]:
    """Get configuration for all automotive claims analyzers."""
    return {
        "autoClaimsDocAnalyzer": {
            "description": "Automotive claims document analyzer for claims forms, repair estimates, and police reports",
            "baseAnalyzerId": "prebuilt-document",
            "fieldSchema": AUTO_CLAIMS_DOC_ANALYZER_SCHEMA,
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
        "autoClaimsImageAnalyzer": {
            "description": "Automotive claims image analyzer for vehicle damage assessment",
            "baseAnalyzerId": "prebuilt-image",
            "fieldSchema": AUTO_CLAIMS_IMAGE_ANALYZER_SCHEMA,
            "config": {
                "returnDetails": True,
                "estimateFieldSourceAndConfidence": True,
            },
            "models": {
                "completion": "gpt-4.1",
            },
        },
        "autoClaimsVideoAnalyzer": {
            "description": "Automotive claims video analyzer for incident footage analysis",
            "baseAnalyzerId": "prebuilt-video",
            "fieldSchema": AUTO_CLAIMS_VIDEO_ANALYZER_SCHEMA,
            "config": {
                "returnDetails": True,
                "enableTranscription": True,
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
    
    headers = {"x-ms-useragent": "automotive-claims-setup"}
    
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
    
    # Handle async operation
    if response.status_code == 202:
        return poll_operation(response, headers)
    
    return response.json() if response.text else {"analyzerId": analyzer_id, "status": "succeeded"}


def update_analyzer(analyzer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing analyzer (delete and recreate)."""
    delete_analyzer(analyzer_id)
    time.sleep(2)  # Wait for deletion to propagate
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


def poll_operation(response, headers: Dict[str, str], timeout_seconds: int = 120) -> Dict[str, Any]:
    """Poll an async operation until completion."""
    import requests
    
    operation_location = response.headers.get("operation-location", "")
    if not operation_location:
        raise ValueError("No operation-location header in response")
    
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
        
        poll_response = requests.get(operation_location, headers=headers, timeout=30)
        poll_response.raise_for_status()
        
        result = poll_response.json()
        status = result.get("status", "").lower()
        
        if status == "succeeded":
            return result
        elif status == "failed":
            raise RuntimeError(f"Operation failed: {result}")
        
        time.sleep(2)


def verify_analyzer(analyzer_id: str, sample_content: bytes, content_type: str) -> bool:
    """Verify an analyzer works with sample content."""
    import requests
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    
    headers = get_auth_headers()
    headers["Content-Type"] = "application/octet-stream"
    
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
    params = {"api-version": api_version}
    
    try:
        response = requests.post(url, headers=headers, params=params, data=sample_content, timeout=60)
        response.raise_for_status()
        
        # Poll for result
        result = poll_operation(response, headers, timeout_seconds=180)
        return result.get("status", "").lower() == "succeeded"
    except Exception as e:
        print(f"  ⚠️  Verification failed: {e}")
        return False


# =============================================================================
# Deployment Functions
# =============================================================================

def deploy_analyzers(force: bool = False) -> bool:
    """Deploy all automotive claims analyzers."""
    configs = get_analyzer_configs()
    success = True
    
    print("\n" + "="*60)
    print("Deploying Automotive Claims Analyzers")
    print("="*60)
    
    for analyzer_id, config in configs.items():
        print(f"\n📦 {analyzer_id}")
        print(f"   Base: {config['baseAnalyzerId']}")
        
        try:
            existing = get_analyzer(analyzer_id)
            
            if existing and not force:
                print("   ✅ Already exists (use --force to recreate)")
                continue
            
            if existing:
                print("   🔄 Updating existing analyzer...")
                result = update_analyzer(analyzer_id, config)
            else:
                print("   ➕ Creating new analyzer...")
                result = create_analyzer(analyzer_id, config)
            
            print("   ✅ Deployed successfully")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            success = False
    
    return success


def verify_all_analyzers() -> bool:
    """Verify all analyzers are deployed and working."""
    configs = get_analyzer_configs()
    
    print("\n" + "="*60)
    print("Verifying Automotive Claims Analyzers")
    print("="*60)
    
    all_exist = True
    for analyzer_id in configs:
        print(f"\n🔍 {analyzer_id}")
        
        try:
            existing = get_analyzer(analyzer_id)
            if existing:
                print("   ✅ Exists")
            else:
                print("   ❌ Not found")
                all_exist = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_exist = False
    
    return all_exist


def delete_all_analyzers() -> bool:
    """Delete all automotive claims analyzers."""
    configs = get_analyzer_configs()
    
    print("\n" + "="*60)
    print("Deleting Automotive Claims Analyzers")
    print("="*60)
    
    for analyzer_id in configs:
        print(f"\n🗑️  {analyzer_id}")
        
        try:
            if delete_analyzer(analyzer_id):
                print("   ✅ Deleted")
            else:
                print("   ⏭️  Not found (already deleted)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True


# =============================================================================
# CLI
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Automotive Claims Custom Analyzers for Azure Content Understanding"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify analyzers exist, don't create/update",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete all automotive claims analyzers",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate even if analyzers exist",
    )
    
    args = parser.parse_args()
    
    # Check environment
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
    if not endpoint:
        print("❌ AZURE_CONTENT_UNDERSTANDING_ENDPOINT not set")
        print("   Set this environment variable to your Azure AI Services endpoint")
        sys.exit(1)
    
    print(f"🔗 Endpoint: {endpoint}")
    
    try:
        if args.delete:
            success = delete_all_analyzers()
        elif args.verify:
            success = verify_all_analyzers()
        else:
            success = deploy_analyzers(force=args.force)
        
        if success:
            print("\n✅ Operation completed successfully")
        else:
            print("\n⚠️  Operation completed with errors")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
