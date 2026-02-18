# Feature Specification: Automotive Claims Multimodal Processing

**Feature Branch**: `007-automotive-claims-multimodal`  
**Created**: 2026-01-20  
**Status**: Draft  
**Input**: User description: "Transform the Property Casualty Claims persona into an Automotive Claims persona leveraging Azure Content Understanding's image and video prebuilt analyzers for multimodal input (documents, images, videos). Implement claims policy rules similar to life/health underwriting policies that rate claims and determine payouts."

---

## Overview

This specification defines a new **Automotive Claims** persona that replaces the existing Property Casualty Claims persona. The key innovation is multimodal content processing, enabling claims adjusters to upload:

1. **Documents** - Claim forms, police reports, repair estimates, invoices
2. **Images** - Vehicle damage photos, accident scene photos, before/after images
3. **Videos** - Dashcam footage, security camera recordings, video walkarounds

Azure Content Understanding's prebuilt analyzers (`prebuilt-documentSearch`, `prebuilt-imageSearch`, `prebuilt-videoSearch`) will be orchestrated to process each media type appropriately, extracting structured data for AI-powered claims assessment.

### Goals

1. **Multimodal Processing** - Automatically detect and route documents, images, and videos to appropriate Azure CU analyzers
2. **Unified Schema Extraction** - Extract automotive claims-specific fields across all media types into a unified data model
3. **AI-Powered Claims Rating** - Apply policy rules to rate claims severity, estimate liability, and determine payout recommendations
4. **Claims Adjuster UX** - Present extracted data, AI analysis, and evidence in a streamlined review interface
5. **Policy Rule Engine** - Define automotive claims policies (similar to life/health underwriting) for consistent, auditable decisions

---

## User Stories

### US-1: Multimodal File Upload via Admin View (Priority: P0)
> As an admin, I want to upload documents, images, and videos related to an automotive claim via the admin view, so that all evidence is processed and analyzed together.

**Why this priority**: Core capability - without multimodal upload, no differentiation from current implementation.

**Note**: File uploads for automotive claims follow the same admin view pattern used for other personas. The admin uploads files which are then processed and available for claims adjusters to review.

**Acceptance Scenarios**:
1. **Given** an admin uploads a PDF police report via admin view, **When** processing starts, **Then** the system routes it to `prebuilt-documentSearch` analyzer.
2. **Given** an admin uploads vehicle damage photos (JPEG/PNG) via admin view, **When** processing starts, **Then** the system routes them to `prebuilt-imageSearch` analyzer.
3. **Given** an admin uploads dashcam footage (MP4) via admin view, **When** processing starts, **Then** the system routes it to `prebuilt-videoSearch` analyzer.
4. **Given** mixed media types are uploaded via admin view, **When** all processing completes, **Then** results are aggregated into a single claim view.

---

### US-2: Automotive Damage Detection from Images (Priority: P0)
> As a claims adjuster, I want AI to analyze vehicle damage photos and identify damage areas, severity, and affected components, so that I can quickly assess repair needs.

**Why this priority**: Primary value proposition for image analysis.

**Acceptance Scenarios**:
1. **Given** vehicle damage images are uploaded, **When** analyzed, **Then** the system extracts damage descriptions including location (front, rear, side), type (dent, scratch, crack), and severity (minor, moderate, severe).
2. **Given** multiple damage photos, **When** analyzed, **Then** each photo is summarized with detected damage areas mapped to vehicle components.
3. **Given** image analysis completes, **When** viewing the claim, **Then** damage areas are highlighted and categorized in the UI.

---

### US-3: Video Evidence Analysis (Priority: P0)
> As a claims adjuster, I want AI to analyze accident footage and extract key moments, transcript, and scene descriptions, so that I understand the incident timeline without watching the full video.

**Why this priority**: Video is high-value evidence but time-consuming to review manually.

**Acceptance Scenarios**:
1. **Given** dashcam video is uploaded, **When** analyzed, **Then** the system extracts transcript (if audio present), keyframes, and segment descriptions.
2. **Given** video analysis completes, **When** viewing the claim, **Then** keyframes are displayed with timestamps and AI-generated scene descriptions.
3. **Given** a collision is visible in video, **When** analyzed, **Then** the system identifies impact moment and describes pre/post-collision events.

---

### US-4: Structured Field Extraction (Priority: P0)
> As a claims adjuster, I want the system to extract standard automotive claim fields (vehicle info, damage estimate, parties involved) from all media types, so that I have structured data for processing.

**Why this priority**: Foundation for policy rule application and downstream processing.

**Acceptance Scenarios**:
1. **Given** a claim with documents and images, **When** extraction completes, **Then** vehicle details (make, model, year, VIN) are extracted with source attribution.
2. **Given** repair estimates in documents, **When** extracted, **Then** line items, labor costs, and parts costs are structured as JSON.
3. **Given** conflicting data across sources, **When** displayed, **Then** the system shows all values with their sources for adjuster resolution.

---

### US-5: Claims Policy Rules and Rating (Priority: P1)
> As a claims adjuster, I want the system to apply automotive claims policies to rate the claim severity and suggest payout, so that I have consistent, policy-based recommendations.

**Why this priority**: Differentiated capability - AI-powered decision support.

**Acceptance Scenarios**:
1. **Given** extracted claim data, **When** policy rules are applied, **Then** the system returns severity rating (Low/Medium/High/Critical) with rationale.
2. **Given** damage assessment and repair estimate, **When** rules are applied, **Then** the system validates estimate against damage severity and flags discrepancies.
3. **Given** liability indicators (video, police report), **When** rules are applied, **Then** the system suggests liability split percentage with evidence citations.
4. **Given** all analysis is complete, **When** viewing the claim, **Then** the adjuster sees recommended payout range with policy references.

---

### US-6: Evidence Review UX (Priority: P1)
> As a claims adjuster, I want a unified view showing all uploaded media, extracted data, and AI analysis, so that I can efficiently review and approve claims.

**Why this priority**: UX is critical for adoption by claims adjusters.

**Acceptance Scenarios**:
1. **Given** a processed claim, **When** viewing the overview, **Then** I see a summary of all uploaded files by type (documents, images, videos).
2. **Given** images were analyzed, **When** viewing the damage section, **Then** I see thumbnails with damage annotations and severity badges.
3. **Given** video was analyzed, **When** viewing the timeline section, **Then** I see keyframes with timestamps and can click to jump to that moment.
4. **Given** policy rules were applied, **When** viewing the decision section, **Then** I see severity rating, payout recommendation, and policy citations.

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Automotive Claims Interface                                          │    │
│  │ - Evidence gallery (images, video keyframes)                         │    │
│  │ - Damage assessment view                                              │    │
│  │ - Policy-based rating display                                         │    │
│  │ (File upload via Admin View - same pattern as other personas)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ Upload Endpoint    │  │ Multimodal Router  │  │ Claims Policy      │    │
│  │ /api/.../upload    │─▶│ - MIME detection   │  │ Engine             │    │
│  │                    │  │ - Analyzer routing │  │ - Rule evaluation  │    │
│  └────────────────────┘  └────────────────────┘  │ - Payout calc      │    │
│                                    │             └────────────────────┘    │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   Azure Content Understanding                        │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │ prebuilt-      │  │ prebuilt-      │  │ prebuilt-              │ │    │
│  │  │ documentSearch │  │ imageSearch    │  │ videoSearch            │ │    │
│  │  │ (PDFs, forms)  │  │ (photos)       │  │ (dashcam, CCTV)        │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┴───────────────────────────────────┐    │
│  │              Automotive Claims Custom Analyzers                      │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │ autoClaimsDoc  │  │ autoClaimsImage│  │ autoClaimsVideo        │ │    │
│  │  │ (field schema) │  │ (damage detect)│  │ (incident analysis)    │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure PostgreSQL Flexible Server                         │
│                          (with pgvector extension)                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Schema: workbenchiq                                                   │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │ claims          │  │ claim_media     │  │ claim_policy_chunks │   │   │
│  │  │ - id (PK)       │  │ - id (PK)       │  │ - id (PK)           │   │   │
│  │  │ - claim_data    │  │ - media_type    │  │ - policy_id         │   │   │
│  │  │ - severity      │  │ - analysis_json │  │ - embedding VECTOR  │   │   │
│  │  │ - payout_rec    │  │ - keyframes     │  │ - category          │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Blob Storage                                       │
│  - Uploaded files (PDFs, images, videos)                                     │
│  - Video keyframes extracted by CU                                           │
│  - CU raw analysis results                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multimodal Processing Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────────┐
│   Upload     │     │   MIME Type  │     │         Analyzer Router          │
│   Files      │────▶│   Detection  │────▶│                                  │
└──────────────┘     └──────────────┘     │  ┌─────────┐ ┌─────────┐        │
                                          │  │ PDF/DOC │ │ JPG/PNG │        │
                                          │  └────┬────┘ └────┬────┘        │
                                          │       │           │              │
                                          │  ┌────▼────┐ ┌────▼────┐        │
                                          │  │Document │ │ Image   │        │
                                          │  │Analyzer │ │Analyzer │        │
                                          │  └─────────┘ └─────────┘        │
                                          │                                  │
                                          │  ┌─────────┐                     │
                                          │  │ MP4/MOV │                     │
                                          │  └────┬────┘                     │
                                          │       │                          │
                                          │  ┌────▼────┐                     │
                                          │  │ Video   │                     │
                                          │  │Analyzer │                     │
                                          │  └─────────┘                     │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │       Result Aggregator          │
                                          │  - Merge extracted fields        │
                                          │  - Combine damage assessments    │
                                          │  - Build unified claim view      │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │    Claims Policy Engine          │
                                          │  - Apply rating rules            │
                                          │  - Calculate severity            │
                                          │  - Generate payout recommendation│
                                          └──────────────────────────────────┘
```

---

## Data Model

### Automotive Claims Field Schema

The following fields are extracted from documents, images, and videos:

#### Vehicle Information
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `VehicleVIN` | string | Vehicle Identification Number | Document, Image (VIN plate) |
| `VehicleMake` | string | Vehicle manufacturer | Document, Image |
| `VehicleModel` | string | Vehicle model name | Document, Image |
| `VehicleYear` | number | Model year | Document, Image |
| `VehicleColor` | string | Vehicle color | Image |
| `LicensePlate` | string | License plate number | Document, Image, Video |
| `Mileage` | string | Odometer reading at time of incident | Document |

#### Incident Information
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `DateOfLoss` | date | Date of the incident | Document |
| `TimeOfLoss` | string | Time of incident | Document, Video |
| `IncidentLocation` | string | Location/address of incident | Document |
| `WeatherConditions` | string | Weather at time of incident | Document, Video |
| `RoadConditions` | string | Road surface conditions | Document, Video |
| `IncidentDescription` | string | Narrative of what happened | Document, Video |
| `PoliceReportNumber` | string | Police report reference | Document |
| `PoliceReportFiled` | boolean | Whether police report was filed | Document |

#### Damage Assessment (Image-Derived)
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `DamageAreas` | array | List of damaged areas | Image |
| `DamageArea.location` | string | Where on vehicle (front, rear, driver_side, passenger_side, roof, hood, trunk) | Image |
| `DamageArea.type` | string | Type of damage (dent, scratch, crack, shattered, crushed, missing_part) | Image |
| `DamageArea.severity` | string | Severity (minor, moderate, severe, total_loss) | Image |
| `DamageArea.components` | array | Affected components (bumper, fender, door, headlight, etc.) | Image |
| `DamageArea.description` | string | AI-generated description | Image |
| `OverallDamageSeverity` | string | Aggregated severity rating | Image (computed) |
| `EstimatedDamageCategory` | string | Light (<$1000), Moderate ($1K-$5K), Heavy ($5K-$15K), Severe (>$15K) | Image (computed) |

#### Video Evidence (Video-Derived)
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `VideoSegments` | array | Video chapter segments | Video |
| `VideoSegment.timestamp` | string | Start timestamp (HH:MM:SS) | Video |
| `VideoSegment.duration` | string | Segment duration | Video |
| `VideoSegment.description` | string | AI scene description | Video |
| `VideoSegment.keyframeUrl` | string | URL to keyframe image | Video |
| `Transcript` | string | Audio transcript if available | Video |
| `ImpactDetected` | boolean | Whether collision/impact was detected | Video |
| `ImpactTimestamp` | string | Timestamp of detected impact | Video |
| `PreIncidentBehavior` | string | Description of events before incident | Video |
| `PostIncidentBehavior` | string | Description of events after incident | Video |

#### Repair Estimate (Document-Derived)
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `EstimateTotal` | string | Total repair estimate | Document |
| `PartsTotal` | string | Total parts cost | Document |
| `LaborTotal` | string | Total labor cost | Document |
| `LaborHours` | number | Total labor hours | Document |
| `LaborRate` | string | Hourly labor rate | Document |
| `RepairLineItems` | array | Individual repair items | Document |
| `RepairLineItem.description` | string | Repair item description | Document |
| `RepairLineItem.quantity` | number | Quantity | Document |
| `RepairLineItem.unitPrice` | string | Price per unit | Document |
| `RepairLineItem.totalPrice` | string | Line total | Document |
| `RepairLineItem.type` | string | parts, labor, paint, other | Document |
| `RepairShopName` | string | Name of repair facility | Document |
| `RepairShopEstimateNumber` | string | Shop's estimate reference | Document |

#### Parties Involved
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `Claimant` | object | Person filing claim | Document |
| `Claimant.name` | string | Full name | Document |
| `Claimant.phone` | string | Phone number | Document |
| `Claimant.email` | string | Email address | Document |
| `Claimant.role` | string | Driver, Passenger, Pedestrian, Property Owner | Document |
| `OtherParties` | array | Other parties involved | Document |
| `Witnesses` | array | Witness information | Document |

#### Policy & Coverage
| Field | Type | Description | Sources |
|-------|------|-------------|---------|
| `PolicyNumber` | string | Insurance policy number | Document |
| `CoverageType` | string | Collision, Comprehensive, Liability, etc. | Document |
| `PolicyLimits` | string | Coverage limits | Document |
| `Deductible` | string | Applicable deductible | Document |

#### AI-Computed Fields (Policy Engine Output)
| Field | Type | Description | Computed |
|-------|------|-------------|----------|
| `SeverityRating` | string | Low, Medium, High, Critical | Yes |
| `LiabilityAssessment` | string | Clear Liability, Shared, Disputed | Yes |
| `LiabilityPercentage` | number | Insured's liability % (0-100) | Yes |
| `PayoutRecommendation` | object | Recommended payout details | Yes |
| `PayoutRecommendation.minAmount` | string | Low end of range | Yes |
| `PayoutRecommendation.maxAmount` | string | High end of range | Yes |
| `PayoutRecommendation.recommendedAmount` | string | Suggested payout | Yes |
| `PolicyRulesApplied` | array | List of policy rules that were applied | Yes |
| `FraudIndicators` | array | Red flags identified | Yes |
| `AdjusterNotes` | string | AI-generated summary for adjuster | Yes |

---

## Automotive Claims Policies

The policy rules follow the same structure as life/health underwriting policies, stored in `data/automotive-claims-policies.json`.

### Policy Categories

| Category | Description |
|----------|-------------|
| `damage_assessment` | Rules for evaluating damage severity and repair estimates |
| `liability` | Rules for determining liability based on evidence |
| `fraud_detection` | Rules for identifying potential fraud indicators |
| `payout_calculation` | Rules for calculating appropriate payout amounts |
| `repair_validation` | Rules for validating repair estimates against damage |

### Example Policies

```json
{
  "version": "1.0",
  "effective_date": "2026-01-01",
  "description": "Automotive Claims Assessment Policies",
  "policies": [
    {
      "id": "DMG-SEV-001",
      "category": "damage_assessment",
      "subcategory": "severity_rating",
      "name": "Damage Severity Classification",
      "description": "Guidelines for classifying vehicle damage severity based on visual assessment",
      "criteria": [
        {
          "id": "DMG-SEV-001-A",
          "condition": "Single minor dent OR scratch < 6 inches AND no structural damage",
          "severity": "Minor",
          "action": "Standard processing, estimated repair $0-$1,000",
          "rationale": "Cosmetic damage only, no safety implications"
        },
        {
          "id": "DMG-SEV-001-B",
          "condition": "Multiple dents OR panel damage OR single component replacement",
          "severity": "Moderate",
          "action": "Standard processing, estimated repair $1,000-$5,000",
          "rationale": "Repairable damage, single panel or component affected"
        },
        {
          "id": "DMG-SEV-001-C",
          "condition": "Multiple panel damage OR structural component affected OR airbag deployment",
          "severity": "Heavy",
          "action": "Senior adjuster review, estimated repair $5,000-$15,000",
          "rationale": "Significant damage requiring frame/structural assessment"
        },
        {
          "id": "DMG-SEV-001-D",
          "condition": "Repair cost > 70% of vehicle value OR frame damage OR safety systems compromised",
          "severity": "Total Loss",
          "action": "Total loss evaluation, market value assessment required",
          "rationale": "Economically unviable to repair, total loss settlement"
        }
      ],
      "modifying_factors": [
        {
          "factor": "Vehicle age",
          "impact": "Vehicles > 10 years lower threshold for total loss (60% of value)"
        },
        {
          "factor": "Prior damage",
          "impact": "Pre-existing damage reduces payout by appraised diminution"
        },
        {
          "factor": "Aftermarket parts",
          "impact": "OEM vs aftermarket parts affects estimate by 10-25%"
        }
      ]
    },
    {
      "id": "LIA-001",
      "category": "liability",
      "subcategory": "fault_determination",
      "name": "Liability Assessment",
      "description": "Guidelines for determining fault and liability percentage",
      "criteria": [
        {
          "id": "LIA-001-A",
          "condition": "Rear-end collision AND no contributing factors from lead vehicle",
          "liability_determination": "Following vehicle 100% at fault",
          "action": "Clear liability, expedited processing",
          "rationale": "Following vehicle responsible for maintaining safe distance"
        },
        {
          "id": "LIA-001-B",
          "condition": "Intersection collision AND traffic signal present",
          "liability_determination": "Determined by signal status and entry sequence",
          "action": "Review police report and witness statements",
          "rationale": "Traffic control determines right of way"
        },
        {
          "id": "LIA-001-C",
          "condition": "Parking lot collision",
          "liability_determination": "Moving vehicle typically at fault, 50/50 if both moving",
          "action": "Review diagram and witness statements",
          "rationale": "Parked vehicles have no contributory negligence"
        },
        {
          "id": "LIA-001-D",
          "condition": "Multi-vehicle collision (3+ vehicles)",
          "liability_determination": "Chain reaction analysis required",
          "action": "Detailed investigation, possible subrogation",
          "rationale": "Complex liability may involve multiple at-fault parties"
        }
      ]
    },
    {
      "id": "FRD-001",
      "category": "fraud_detection",
      "subcategory": "red_flags",
      "name": "Fraud Indicator Detection",
      "description": "Guidelines for identifying potential fraudulent claims",
      "criteria": [
        {
          "id": "FRD-001-A",
          "condition": "Claim filed within 30 days of policy inception",
          "risk_level": "High",
          "action": "SIU referral, enhanced documentation review",
          "rationale": "New policies have higher fraud incidence"
        },
        {
          "id": "FRD-001-B",
          "condition": "Repair estimate exceeds visible damage by > 50%",
          "risk_level": "Moderate",
          "action": "Independent appraisal required",
          "rationale": "Estimate inflation is common fraud pattern"
        },
        {
          "id": "FRD-001-C",
          "condition": "Multiple claims in 12-month period (> 2)",
          "risk_level": "Moderate",
          "action": "Claims history review, pattern analysis",
          "rationale": "Frequent claims may indicate fraud or abuse"
        },
        {
          "id": "FRD-001-D",
          "condition": "Damage inconsistent with described incident",
          "risk_level": "High",
          "action": "SIU referral, photo analysis, possible EUO",
          "rationale": "Staged accidents have damage patterns that don't match narrative"
        },
        {
          "id": "FRD-001-E",
          "condition": "No police report for significant damage claim",
          "risk_level": "Low-Moderate",
          "action": "Request explanation, verify with claimant",
          "rationale": "Legitimate claims typically have police documentation"
        }
      ]
    },
    {
      "id": "PAY-001",
      "category": "payout_calculation",
      "subcategory": "estimate_validation",
      "name": "Repair Estimate Validation",
      "description": "Guidelines for validating and adjusting repair estimates",
      "criteria": [
        {
          "id": "PAY-001-A",
          "condition": "Estimate within 10% of AI damage assessment",
          "action": "Approve estimate as submitted",
          "rationale": "Estimate aligns with damage severity, no adjustment needed"
        },
        {
          "id": "PAY-001-B",
          "condition": "Estimate exceeds AI assessment by 10-25%",
          "action": "Review line items, request photo documentation for discrepancies",
          "rationale": "Minor discrepancy, may be legitimate hidden damage"
        },
        {
          "id": "PAY-001-C",
          "condition": "Estimate exceeds AI assessment by > 25%",
          "action": "Independent appraisal required, negotiate or deny excess",
          "rationale": "Significant discrepancy requires independent verification"
        },
        {
          "id": "PAY-001-D",
          "condition": "Labor rate exceeds market rate by > 15%",
          "action": "Adjust to prevailing market rate for region",
          "rationale": "Pay reasonable labor rates per market analysis"
        }
      ]
    }
  ]
}
```

---

## Requirements

### Functional Requirements

#### Multimodal Processing (P0)
- **FR-001**: System MUST detect file MIME type on upload (document/image/video).
- **FR-002**: System MUST route documents (PDF, DOC, DOCX) to `prebuilt-documentSearch` or custom document analyzer.
- **FR-003**: System MUST route images (JPEG, PNG, GIF, WEBP) to `prebuilt-imageSearch` or custom image analyzer.
- **FR-004**: System MUST route videos (MP4, MOV, AVI, WEBM) to `prebuilt-videoSearch` or custom video analyzer.
- **FR-005**: System MUST support parallel processing of multiple files with different types.
- **FR-006**: System MUST aggregate results from all analyzers into unified claim data.

#### Field Extraction (P0)
- **FR-007**: System MUST extract vehicle information fields from documents and images.
- **FR-008**: System MUST extract damage assessments from images with location, type, and severity.
- **FR-009**: System MUST extract video segments, keyframes, and transcripts from videos.
- **FR-010**: System MUST extract repair estimate line items from documents.
- **FR-011**: System MUST preserve source attribution for each extracted field.

#### Custom Analyzers (P0)
- **FR-012**: System MUST create custom document analyzer (`autoClaimsDocAnalyzer`) extending `prebuilt-document` with automotive claims field schema.
- **FR-013**: System MUST create custom image analyzer (`autoClaimsImageAnalyzer`) extending `prebuilt-image` for damage detection.
- **FR-014**: System MUST create custom video analyzer (`autoClaimsVideoAnalyzer`) extending `prebuilt-video` for incident analysis.

#### Policy Engine (P1)
- **FR-015**: System MUST load automotive claims policies from JSON file.
- **FR-016**: System MUST apply damage assessment policies to rate severity.
- **FR-017**: System MUST apply liability policies to determine fault percentage.
- **FR-018**: System MUST apply fraud detection policies to identify red flags.
- **FR-019**: System MUST apply payout policies to validate estimates and calculate recommendations.
- **FR-020**: System MUST provide policy citations for all AI-generated recommendations.

#### RAG Integration (P1)
- **FR-021**: System MUST chunk and embed automotive claims policies (similar to life/health policies).
- **FR-022**: System MUST support semantic search over automotive claims policies in Ask IQ.
- **FR-023**: System MUST retrieve relevant policy chunks for claims questions.

#### UX (P1)
- **FR-024**: Frontend MUST display evidence gallery with images and video keyframes.
- **FR-025**: Frontend MUST show damage assessment with visual annotations.
- **FR-026**: Frontend MUST display video timeline with clickable keyframes.
- **FR-027**: Frontend MUST show policy-based recommendations with severity and payout.
- **FR-028**: Frontend MUST allow adjuster to approve/adjust/reject AI recommendations.

#### Admin View (P0)
- **FR-029**: Admin view MUST support multimodal file upload (documents, images, videos) - consistent with other personas.
- **FR-030**: Admin view MUST allow policy JSON file updates (upload/replace `automotive-claims-policies.json`).
- **FR-031**: Admin view MUST allow custom analyzer configuration updates.

### Non-Functional Requirements

- **NFR-001**: Image analysis MUST complete within 30 seconds per image.
- **NFR-002**: Video analysis MUST complete within 2 minutes per minute of video content.
- **NFR-003**: Document analysis MUST complete within 30 seconds per document.
- **NFR-004**: Total claim processing (all files) MUST complete within 5 minutes.
- **NFR-005**: System MUST support videos up to 10 minutes in length.
- **NFR-006**: System MUST support images up to 20MB.
- **NFR-007**: Video keyframes MUST be stored in blob storage and accessible via URL.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTO_CLAIMS_ENABLED` | No | `true` | Enable automotive claims persona |
| `AUTO_CLAIMS_DOC_ANALYZER` | No | `autoClaimsDocAnalyzer` | Custom document analyzer ID |
| `AUTO_CLAIMS_IMAGE_ANALYZER` | No | `autoClaimsImageAnalyzer` | Custom image analyzer ID |
| `AUTO_CLAIMS_VIDEO_ANALYZER` | No | `autoClaimsVideoAnalyzer` | Custom video analyzer ID |
| `AUTO_CLAIMS_POLICIES_PATH` | No | `data/automotive-claims-policies.json` | Path to claims policies |
| `VIDEO_MAX_DURATION_MINUTES` | No | `10` | Maximum video duration allowed |
| `IMAGE_MAX_SIZE_MB` | No | `20` | Maximum image file size |

### Azure Content Understanding Analyzer Setup

The custom analyzers must be created in Azure Content Understanding before use. See `scripts/setup_automotive_analyzers.py` for automated setup.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 95%+ of uploaded files correctly routed to appropriate analyzer.
- **SC-002**: Damage detection accuracy of 85%+ (validated against adjuster review).
- **SC-003**: Policy rule application provides recommendation for 90%+ of processed claims.
- **SC-004**: Claims processing time reduced by 40% compared to manual review.
- **SC-005**: Adjuster satisfaction rating of 4+/5 for AI assistance quality.

---

## Assumptions

1. Azure Content Understanding supports the prebuilt image and video analyzers in GA API (2025-11-01).
2. Video files are compressed to reasonable sizes before upload (< 500MB).
3. Claims adjusters have training on interpreting AI damage assessments.
4. Automotive claims policies are defined and approved by claims leadership.
5. Storage costs for video keyframes are acceptable.

---

## Open Questions

1. **Q**: Should we support real-time video streaming analysis or only uploaded files?
   - **Proposed**: Uploaded files only for MVP, streaming deferred to future.

2. **Q**: How should conflicting field extractions across media types be resolved?
   - **Proposed**: Show all values with sources, highest-confidence value as default.

3. **Q**: Should payout recommendations include historical comparison?
   - **Proposed**: Defer to Phase 2, focus on policy-based calculation first.

4. **Q**: What video formats must be supported?
   - **Proposed**: MP4 (H.264) as primary, MOV as secondary, others via transcoding.

---

## Future Enhancements (Out of Scope)

1. **Real-time damage annotation** - Allow adjusters to draw on images.
2. **3D vehicle damage mapping** - Map damage to 3D vehicle model.
3. **Telematics integration** - Import OBD-II/telematics data for incident reconstruction.
4. **Voice-to-text claim intake** - Phone call transcription for FNOL.
5. **Repair shop network integration** - Direct estimate submission from preferred shops.
6. **Subrogation automation** - Automated demand letter generation.
