# Research: Automotive Claims Multimodal Processing

**Feature**: 007-automotive-claims-multimodal  
**Date**: 2026-01-20  
**Status**: Complete

---

## Executive Summary

This document captures research findings for implementing multimodal automotive claims processing using Azure Content Understanding (CU) image and video analyzers. Key findings:

1. **Azure CU supports multimodal content** - prebuilt analyzers available for documents, images, audio, and video
2. **Custom analyzers can be derived** from base prebuilt analyzers to add domain-specific field schemas
3. **Video processing provides rich output** - transcripts, keyframes, segments, and scene descriptions
4. **Image analysis requires customization** for damage detection - prebuilt only provides descriptions

---

## Azure Content Understanding Analyzers

### Available Prebuilt Analyzers

| Analyzer ID | Content Type | Purpose | GA Status |
|-------------|--------------|---------|-----------|
| `prebuilt-documentSearch` | Documents | RAG-optimized extraction with markdown | ✅ GA |
| `prebuilt-imageSearch` | Images | Description generation for search | ✅ GA |
| `prebuilt-videoSearch` | Videos | Transcript, keyframes, segments | ✅ GA |
| `prebuilt-audioSearch` | Audio | Transcript, summary | ✅ GA |
| `prebuilt-document` | Documents | Base document analyzer | ✅ GA |
| `prebuilt-image` | Images | Base image analyzer | ✅ GA |
| `prebuilt-video` | Videos | Base video analyzer | ✅ GA |

### Base Analyzers for Custom Derivation

To create custom analyzers with domain-specific field extraction, derive from these base analyzers:

- `prebuilt-document` - For custom document field extraction
- `prebuilt-image` - For custom image field extraction  
- `prebuilt-video` - For custom video field extraction

### API Version

Use GA API version: `2025-11-01`

---

## Image Analysis Capabilities

### prebuilt-imageSearch Output

The `prebuilt-imageSearch` analyzer provides:

```json
{
  "result": {
    "contents": [
      {
        "kind": "image",
        "markdown": "A photograph showing a silver sedan with damage to the front bumper...",
        "fields": {}
      }
    ]
  }
}
```

**Limitations**:
- Only provides natural language description
- No structured damage detection fields
- No bounding boxes for damage areas
- Requires custom analyzer for automotive-specific extraction

### Custom Image Analyzer Schema

To extract structured damage data, create a custom analyzer:

```json
{
  "analyzerId": "autoClaimsImageAnalyzer",
  "name": "Automotive Claims Image Analyzer",
  "description": "Analyzes vehicle damage photos for automotive insurance claims. Detects damage areas, severity, and affected components.",
  "baseAnalyzerId": "prebuilt-image",
  "fieldSchema": {
    "fields": {
      "DamageAreas": {
        "type": "array",
        "description": "List of detected damage areas on the vehicle",
        "method": "generate",
        "items": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "Location on vehicle: front, rear, driver_side, passenger_side, roof, hood, trunk"
            },
            "damageType": {
              "type": "string", 
              "description": "Type of damage: dent, scratch, crack, shattered, crushed, missing_part"
            },
            "severity": {
              "type": "string",
              "description": "Severity level: minor, moderate, severe"
            },
            "components": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Affected components: bumper, fender, door, hood, headlight, taillight, mirror, window, tire, wheel"
            },
            "description": {
              "type": "string",
              "description": "Detailed description of the damage"
            }
          }
        }
      },
      "OverallDamageSeverity": {
        "type": "string",
        "description": "Overall damage severity assessment: minor, moderate, severe, total_loss",
        "method": "generate"
      },
      "VehicleType": {
        "type": "string",
        "description": "Type of vehicle visible: sedan, SUV, truck, van, motorcycle, other",
        "method": "generate"
      },
      "VehicleColor": {
        "type": "string",
        "description": "Primary color of the vehicle",
        "method": "generate"
      },
      "LicensePlateVisible": {
        "type": "boolean",
        "description": "Whether a license plate is visible in the image",
        "method": "generate"
      },
      "LicensePlateNumber": {
        "type": "string",
        "description": "License plate number if visible and readable",
        "method": "extract"
      }
    }
  },
  "config": {
    "disableFaceBlurring": false
  }
}
```

---

## Video Analysis Capabilities

### prebuilt-videoSearch Output Structure

The `prebuilt-videoSearch` analyzer provides rich output:

```json
{
  "result": {
    "contents": [
      {
        "kind": "audioVisual",
        "markdown": "## Video Transcript\n\n[00:00:00] WEBVTT format transcript...\n\n## Segment 1\nDescription of first segment...",
        "transcript": "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nText of speech...",
        "segments": [
          {
            "id": "segment-1",
            "startTimestamp": "00:00:00",
            "endTimestamp": "00:01:30",
            "description": "A silver car is driving on a highway in daylight conditions..."
          }
        ],
        "frames": [
          {
            "timestamp": "00:00:05.000",
            "url": "https://...keyframe-001.jpg",
            "description": "Highway scene with vehicles"
          }
        ]
      }
    ]
  }
}
```

### Video Processing Considerations

1. **Processing Time**: ~1-2 minutes per minute of video content
2. **Keyframe Access**: Keyframe URLs are temporary; download and store in blob storage
3. **Transcript Quality**: Depends on audio quality; dashcams often have poor audio
4. **Segment Granularity**: Auto-segmented based on scene changes

### Custom Video Analyzer Schema

```json
{
  "analyzerId": "autoClaimsVideoAnalyzer",
  "name": "Automotive Claims Video Analyzer",
  "description": "Analyzes dashcam and accident footage for automotive insurance claims. Detects incidents, collisions, and driving behavior.",
  "baseAnalyzerId": "prebuilt-video",
  "fieldSchema": {
    "fields": {
      "IncidentDetected": {
        "type": "boolean",
        "description": "Whether a collision or incident is detected in the video",
        "method": "generate"
      },
      "IncidentTimestamp": {
        "type": "string",
        "description": "Timestamp of the detected incident in HH:MM:SS format",
        "method": "generate"
      },
      "IncidentType": {
        "type": "string",
        "description": "Type of incident: rear_end, sideswipe, head_on, single_vehicle, parking, unknown",
        "method": "generate"
      },
      "PreIncidentBehavior": {
        "type": "string",
        "description": "Description of driving behavior in the 10 seconds before incident",
        "method": "generate"
      },
      "PostIncidentBehavior": {
        "type": "string",
        "description": "Description of events immediately after the incident",
        "method": "generate"
      },
      "WeatherConditions": {
        "type": "string",
        "description": "Weather conditions visible: clear, rain, snow, fog, night",
        "method": "generate"
      },
      "RoadType": {
        "type": "string",
        "description": "Type of road: highway, city_street, parking_lot, intersection, residential",
        "method": "generate"
      },
      "SpeedEstimate": {
        "type": "string",
        "description": "Estimated speed of the recording vehicle if determinable",
        "method": "generate"
      },
      "OtherVehicles": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Other vehicles involved in the incident",
        "method": "generate"
      }
    }
  },
  "config": {
    "enableSegment": true,
    "disableFaceBlurring": false,
    "locales": ["en-US"]
  }
}
```

---

## Document Analysis for Claims

### Custom Document Analyzer Schema

```json
{
  "analyzerId": "autoClaimsDocAnalyzer",
  "name": "Automotive Claims Document Analyzer",
  "description": "Extracts structured data from automotive claims documents including police reports, repair estimates, and claim forms.",
  "baseAnalyzerId": "prebuilt-document",
  "fieldSchema": {
    "fields": {
      "ClaimNumber": {
        "type": "string",
        "description": "Unique claim reference number",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "PolicyNumber": {
        "type": "string",
        "description": "Insurance policy number",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "DateOfLoss": {
        "type": "date",
        "description": "Date when the incident occurred",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "VehicleVIN": {
        "type": "string",
        "description": "Vehicle Identification Number (17 characters)",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "VehicleMake": {
        "type": "string",
        "description": "Vehicle manufacturer (Toyota, Ford, Honda, etc.)",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "VehicleModel": {
        "type": "string",
        "description": "Vehicle model name",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "VehicleYear": {
        "type": "number",
        "description": "Vehicle model year",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "ClaimantName": {
        "type": "string",
        "description": "Full name of the person filing the claim",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "IncidentLocation": {
        "type": "string",
        "description": "Address or location where incident occurred",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "PoliceReportNumber": {
        "type": "string",
        "description": "Police report reference number if available",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "RepairEstimateTotal": {
        "type": "string",
        "description": "Total repair estimate amount with currency",
        "method": "extract",
        "estimateSourceAndConfidence": true
      },
      "RepairLineItems": {
        "type": "array",
        "description": "Individual repair items with descriptions and costs",
        "method": "extract",
        "items": {
          "type": "object",
          "properties": {
            "description": { "type": "string" },
            "quantity": { "type": "number" },
            "unitPrice": { "type": "string" },
            "totalPrice": { "type": "string" },
            "itemType": { "type": "string" }
          }
        }
      },
      "IncidentDescription": {
        "type": "string",
        "description": "Narrative description of how the incident occurred",
        "method": "extract",
        "estimateSourceAndConfidence": true
      }
    }
  },
  "config": {
    "enableOcr": true,
    "enableLayout": true,
    "returnDetails": true,
    "estimateFieldSourceAndConfidence": true
  }
}
```

---

## MIME Type Detection

### File Type to Media Type Mapping

| MIME Type | Extension | Media Type | Analyzer |
|-----------|-----------|------------|----------|
| `application/pdf` | .pdf | document | autoClaimsDocAnalyzer |
| `application/msword` | .doc | document | autoClaimsDocAnalyzer |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx | document | autoClaimsDocAnalyzer |
| `image/jpeg` | .jpg, .jpeg | image | autoClaimsImageAnalyzer |
| `image/png` | .png | image | autoClaimsImageAnalyzer |
| `image/gif` | .gif | image | autoClaimsImageAnalyzer |
| `image/webp` | .webp | image | autoClaimsImageAnalyzer |
| `image/heic` | .heic | image | autoClaimsImageAnalyzer |
| `video/mp4` | .mp4 | video | autoClaimsVideoAnalyzer |
| `video/quicktime` | .mov | video | autoClaimsVideoAnalyzer |
| `video/x-msvideo` | .avi | video | autoClaimsVideoAnalyzer |
| `video/webm` | .webm | video | autoClaimsVideoAnalyzer |

### Python MIME Detection

```python
import mimetypes
from pathlib import Path

DOCUMENT_MIMES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

IMAGE_MIMES = {
    'image/jpeg',
    'image/png', 
    'image/gif',
    'image/webp',
    'image/heic',
}

VIDEO_MIMES = {
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
}

def detect_media_type(filename: str, content_type: str | None = None) -> str:
    """Detect media type from filename or content type."""
    mime = content_type or mimetypes.guess_type(filename)[0]
    
    if mime in DOCUMENT_MIMES:
        return 'document'
    elif mime in IMAGE_MIMES:
        return 'image'
    elif mime in VIDEO_MIMES:
        return 'video'
    else:
        # Fallback to extension
        ext = Path(filename).suffix.lower()
        if ext in {'.pdf', '.doc', '.docx'}:
            return 'document'
        elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic'}:
            return 'image'
        elif ext in {'.mp4', '.mov', '.avi', '.webm'}:
            return 'video'
    
    raise ValueError(f"Unknown media type for {filename}")
```

---

## API Endpoint Patterns

### Analyzer Creation

```http
PUT {endpoint}/contentunderstanding/analyzers/{analyzerId}?api-version=2025-11-01
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Automotive Claims Image Analyzer",
  "description": "...",
  "baseAnalyzerId": "prebuilt-image",
  "fieldSchema": { ... },
  "config": { ... }
}
```

### Analyze Binary (for all content types)

```http
POST {endpoint}/contentunderstanding/analyzers/{analyzerId}:analyzeBinary?api-version=2025-11-01
Authorization: Bearer {token}
Content-Type: application/octet-stream

<binary file content>
```

### Get Analysis Result

```http
GET {operation-location}
Authorization: Bearer {token}
```

---

## Video Keyframe Handling

### Keyframe URL Structure

Keyframe URLs from CU are temporary and follow this pattern:
```
https://{endpoint}/contentunderstanding/analyzerResults/{resultId}/frames/{frameId}?api-version=2025-11-01
```

### Keyframe Download and Storage

```python
import requests
from azure.storage.blob import BlobServiceClient

async def download_and_store_keyframes(keyframes: list, blob_client: BlobServiceClient, container: str, claim_id: str):
    """Download keyframes from CU and store in blob storage."""
    stored_keyframes = []
    
    for idx, kf in enumerate(keyframes):
        # Download from CU
        response = requests.get(kf['url'], headers=headers)
        response.raise_for_status()
        
        # Store in blob
        blob_name = f"claims/{claim_id}/keyframes/frame_{idx:04d}.jpg"
        blob_client.get_blob_client(container, blob_name).upload_blob(
            response.content, 
            overwrite=True
        )
        
        stored_keyframes.append({
            'sequence': idx,
            'timestamp': kf['timestamp'],
            'blob_path': blob_name,
            'description': kf.get('description', '')
        })
    
    return stored_keyframes
```

---

## Performance Considerations

### Processing Time Estimates

| Content Type | Size | Expected Processing Time |
|--------------|------|-------------------------|
| Document (PDF) | 10 pages | 15-30 seconds |
| Image (JPEG) | 5 MB | 5-15 seconds |
| Video (MP4) | 1 minute | 60-120 seconds |
| Video (MP4) | 5 minutes | 5-10 minutes |

### Parallel Processing Strategy

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_claim_files(files: list, settings: Settings):
    """Process multiple files in parallel."""
    # Group by media type for batching
    documents = [f for f in files if f.media_type == 'document']
    images = [f for f in files if f.media_type == 'image']
    videos = [f for f in files if f.media_type == 'video']
    
    # Process in parallel
    async with asyncio.TaskGroup() as tg:
        doc_task = tg.create_task(process_documents(documents, settings))
        img_task = tg.create_task(process_images(images, settings))
        vid_task = tg.create_task(process_videos(videos, settings))
    
    return {
        'documents': doc_task.result(),
        'images': img_task.result(),
        'videos': vid_task.result()
    }
```

---

## Existing Codebase Integration Points

### Content Understanding Client

The existing `app/content_understanding_client.py` has these functions that can be extended:

- `analyze_document()` - Works for all binary content
- `poll_result()` - Works for all async operations
- `extract_markdown_from_result()` - Needs extension for video/image

### Storage Module

The existing `app/storage.py` and `app/storage_providers/` support:
- Local file storage
- Azure Blob storage

Both can store video keyframes and extracted thumbnails.

### Persona Configuration

The existing `app/personas.py` pattern:
- `PersonaType` enum - Add `AUTOMOTIVE_CLAIMS`
- `PERSONA_CONFIGS` dict - Add new persona config
- `get_persona_config()` - Works with new persona

### Processing Pipeline

The existing `app/processing.py` flow:
1. `run_content_understanding_for_files()` - Needs multimodal router
2. `run_underwriting_prompts()` - Works but needs claims-specific prompts

---

## References

1. [Azure Content Understanding Prebuilt Analyzers](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/prebuilt-analyzers)
2. [Create Custom Analyzers](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/tutorial/create-custom-analyzer)
3. [Video Analysis Overview](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/video/overview)
4. [Content Understanding REST API Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/quickstart/use-rest-api)
5. [Analyzer Configuration Reference](https://learn.microsoft.com/en-us/azure/ai-services/content-understanding/concepts/analyzer-reference)
