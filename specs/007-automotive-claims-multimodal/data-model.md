# Data Model: Automotive Claims Multimodal Processing

**Feature**: 007-automotive-claims-multimodal  
**Date**: 2026-01-20  
**Source**: Feature spec entities + multimodal processing requirements

---

## Overview

This document defines the complete data model for automotive claims with multimodal content (documents, images, videos). It extends the existing PostgreSQL schema from spec-006 and adds new entities for media analysis results.

---

## Database Configuration

### Additional Extensions (if not already enabled)

```sql
-- Already required from spec-006
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## Entity Definitions

### 1. claim_media (Multimodal Content Registry)

Stores metadata and analysis results for each uploaded media file.

```sql
CREATE TABLE claim_media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- File identification
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    content_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT,
    
    -- Media classification
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN (
        'document',
        'image',
        'video'
    )),
    
    -- Storage location
    storage_backend VARCHAR(20) NOT NULL DEFAULT 'azure_blob',
    blob_path VARCHAR(500) NOT NULL,
    blob_url TEXT,
    
    -- Analyzer used
    analyzer_id VARCHAR(100) NOT NULL,
    analyzer_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (analyzer_status IN (
        'pending',
        'processing',
        'succeeded',
        'failed'
    )),
    
    -- Analysis results (type-specific JSON)
    analysis_result JSONB,
    extracted_fields JSONB,
    confidence_scores JSONB,
    
    -- Video-specific fields
    duration_seconds INTEGER,
    keyframe_count INTEGER,
    transcript TEXT,
    
    -- Image-specific fields
    image_width INTEGER,
    image_height INTEGER,
    damage_annotations JSONB,
    
    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_claim_media_application ON claim_media (application_id);
CREATE INDEX idx_claim_media_type ON claim_media (media_type);
CREATE INDEX idx_claim_media_status ON claim_media (analyzer_status);
CREATE INDEX idx_claim_media_analysis ON claim_media USING gin (analysis_result);
CREATE INDEX idx_claim_media_fields ON claim_media USING gin (extracted_fields);
```

---

### 2. claim_keyframes (Video Keyframe Registry)

Stores keyframes extracted from video analysis.

```sql
CREATE TABLE claim_keyframes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id UUID NOT NULL REFERENCES claim_media(id) ON DELETE CASCADE,
    application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- Keyframe identification
    sequence_number INTEGER NOT NULL,
    timestamp_seconds DECIMAL(10, 3) NOT NULL,
    timestamp_formatted VARCHAR(20), -- "HH:MM:SS.mmm"
    
    -- Storage
    blob_path VARCHAR(500) NOT NULL,
    blob_url TEXT,
    thumbnail_url TEXT,
    
    -- AI Analysis
    scene_description TEXT,
    detected_objects JSONB, -- Array of detected objects with confidence
    detected_damage JSONB, -- Damage if visible in keyframe
    is_impact_frame BOOLEAN DEFAULT FALSE,
    
    -- Segment association
    segment_id VARCHAR(50),
    segment_description TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_keyframes_media ON claim_keyframes (media_id);
CREATE INDEX idx_keyframes_application ON claim_keyframes (application_id);
CREATE INDEX idx_keyframes_sequence ON claim_keyframes (media_id, sequence_number);
CREATE INDEX idx_keyframes_impact ON claim_keyframes (is_impact_frame) WHERE is_impact_frame = TRUE;
```

---

### 3. claim_damage_areas (Damage Detection Results)

Stores detected damage areas from image analysis.

```sql
CREATE TABLE claim_damage_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id UUID NOT NULL REFERENCES claim_media(id) ON DELETE CASCADE,
    application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- Damage classification
    location VARCHAR(50) NOT NULL, -- front, rear, driver_side, passenger_side, roof, hood, trunk
    damage_type VARCHAR(50) NOT NULL, -- dent, scratch, crack, shattered, crushed, missing_part
    severity VARCHAR(20) NOT NULL, -- minor, moderate, severe, total_loss
    
    -- Affected components
    components JSONB, -- Array of component names: ["bumper", "headlight", "fender"]
    
    -- AI Analysis
    description TEXT,
    confidence DECIMAL(5, 4) NOT NULL, -- 0.0000 to 1.0000
    
    -- Bounding box (normalized coordinates 0-1)
    bbox_x DECIMAL(5, 4),
    bbox_y DECIMAL(5, 4),
    bbox_width DECIMAL(5, 4),
    bbox_height DECIMAL(5, 4),
    
    -- Estimated cost impact
    estimated_repair_min DECIMAL(10, 2),
    estimated_repair_max DECIMAL(10, 2),
    
    -- Adjuster review
    adjuster_confirmed BOOLEAN,
    adjuster_severity_override VARCHAR(20),
    adjuster_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_damage_media ON claim_damage_areas (media_id);
CREATE INDEX idx_damage_application ON claim_damage_areas (application_id);
CREATE INDEX idx_damage_location ON claim_damage_areas (location);
CREATE INDEX idx_damage_severity ON claim_damage_areas (severity);
CREATE INDEX idx_damage_type ON claim_damage_areas (damage_type);
```

---

### 4. claim_repair_items (Repair Estimate Line Items)

Stores parsed repair estimate line items from documents.

```sql
CREATE TABLE claim_repair_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id UUID NOT NULL REFERENCES claim_media(id) ON DELETE CASCADE,
    application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- Line item details
    line_number INTEGER NOT NULL,
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN (
        'parts',
        'labor',
        'paint',
        'materials',
        'sublet',
        'other'
    )),
    
    -- Description and codes
    description TEXT NOT NULL,
    part_number VARCHAR(100),
    oem_part BOOLEAN,
    
    -- Pricing
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2) NOT NULL,
    
    -- Labor specific
    labor_hours DECIMAL(6, 2),
    labor_rate DECIMAL(8, 2),
    labor_type VARCHAR(50), -- body, mechanical, paint, frame
    
    -- Validation
    ai_validated BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,
    market_rate_comparison DECIMAL(5, 2), -- % difference from market rate
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_repair_items_media ON claim_repair_items (media_id);
CREATE INDEX idx_repair_items_application ON claim_repair_items (application_id);
CREATE INDEX idx_repair_items_type ON claim_repair_items (item_type);
```

---

### 5. claim_policy_chunks (Automotive Claims Policy RAG)

Stores chunked automotive claims policies with embeddings (similar to policy_chunks for underwriting).

```sql
CREATE TABLE claim_policy_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Policy identification
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    
    -- Chunk classification
    chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
        'policy_header',
        'criteria',
        'modifying_factor',
        'reference',
        'description'
    )),
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    
    -- Hierarchical metadata for filtering
    category VARCHAR(50) NOT NULL, -- damage_assessment, liability, fraud_detection, payout_calculation
    subcategory VARCHAR(50),
    
    -- Criteria-specific fields
    criteria_id VARCHAR(50),
    severity_level VARCHAR(30),
    action_recommendation TEXT,
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    
    -- Vector embedding
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index for upsert
CREATE UNIQUE INDEX idx_claim_policy_chunks_unique ON claim_policy_chunks 
    (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

-- HNSW index for vector search
CREATE INDEX idx_claim_policy_chunks_embedding ON claim_policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Filtering indexes
CREATE INDEX idx_claim_policy_chunks_category ON claim_policy_chunks (category);
CREATE INDEX idx_claim_policy_chunks_subcategory ON claim_policy_chunks (subcategory);
CREATE INDEX idx_claim_policy_chunks_policy_id ON claim_policy_chunks (policy_id);

-- Full-text search for hybrid search
CREATE INDEX idx_claim_policy_chunks_content_trgm ON claim_policy_chunks 
    USING gin (content gin_trgm_ops);
```

---

### 6. claim_assessments (AI Claim Assessment Results)

Stores the aggregated AI assessment and recommendations for each claim.

```sql
CREATE TABLE claim_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id VARCHAR(36) NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
    
    -- Overall Assessment
    severity_rating VARCHAR(20) NOT NULL CHECK (severity_rating IN (
        'Low',
        'Medium', 
        'High',
        'Critical'
    )),
    severity_rationale TEXT,
    
    -- Liability Assessment
    liability_determination VARCHAR(50), -- Clear Liability, Shared, Disputed, Under Investigation
    insured_liability_percentage INTEGER CHECK (insured_liability_percentage BETWEEN 0 AND 100),
    liability_rationale TEXT,
    liability_evidence JSONB, -- References to supporting evidence
    
    -- Damage Summary
    overall_damage_severity VARCHAR(20),
    total_damage_areas INTEGER,
    affected_components JSONB, -- Array of all affected components
    
    -- Financial Assessment
    total_repair_estimate DECIMAL(12, 2),
    ai_validated_estimate DECIMAL(12, 2),
    estimate_variance_percentage DECIMAL(5, 2),
    
    -- Payout Recommendation
    payout_min DECIMAL(12, 2),
    payout_max DECIMAL(12, 2),
    payout_recommended DECIMAL(12, 2),
    payout_rationale TEXT,
    
    -- Policy Rules Applied
    policies_applied JSONB, -- Array of {policy_id, criteria_id, action, impact}
    
    -- Fraud Assessment
    fraud_risk_level VARCHAR(20), -- Low, Medium, High
    fraud_indicators JSONB, -- Array of {indicator, severity, description}
    siu_referral_recommended BOOLEAN DEFAULT FALSE,
    
    -- Adjuster Actions
    adjuster_decision VARCHAR(50), -- Pending, Approved, Approved with Adjustment, Denied, Under Investigation
    adjuster_decision_date TIMESTAMPTZ,
    adjuster_notes TEXT,
    adjuster_override_amount DECIMAL(12, 2),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_assessments_severity ON claim_assessments (severity_rating);
CREATE INDEX idx_assessments_liability ON claim_assessments (liability_determination);
CREATE INDEX idx_assessments_fraud ON claim_assessments (fraud_risk_level);
CREATE INDEX idx_assessments_decision ON claim_assessments (adjuster_decision);
CREATE INDEX idx_assessments_policies ON claim_assessments USING gin (policies_applied);
```

---

## TypeScript Interfaces

### ClaimMedia Interface

```typescript
interface ClaimMedia {
  id: string;
  applicationId: string;
  filename: string;
  originalFilename: string;
  contentType: string;
  sizeBytes: number;
  mediaType: 'document' | 'image' | 'video';
  storageBackend: 'local' | 'azure_blob';
  blobPath: string;
  blobUrl?: string;
  analyzerId: string;
  analyzerStatus: 'pending' | 'processing' | 'succeeded' | 'failed';
  analysisResult?: Record<string, any>;
  extractedFields?: Record<string, any>;
  confidenceScores?: Record<string, number>;
  // Video-specific
  durationSeconds?: number;
  keyframeCount?: number;
  transcript?: string;
  // Image-specific
  imageWidth?: number;
  imageHeight?: number;
  damageAnnotations?: DamageAnnotation[];
  errorMessage?: string;
  createdAt: string;
  processedAt?: string;
}
```

### ClaimKeyframe Interface

```typescript
interface ClaimKeyframe {
  id: string;
  mediaId: string;
  applicationId: string;
  sequenceNumber: number;
  timestampSeconds: number;
  timestampFormatted: string;
  blobPath: string;
  blobUrl?: string;
  thumbnailUrl?: string;
  sceneDescription?: string;
  detectedObjects?: DetectedObject[];
  detectedDamage?: DamageArea[];
  isImpactFrame: boolean;
  segmentId?: string;
  segmentDescription?: string;
}

interface DetectedObject {
  label: string;
  confidence: number;
  boundingBox?: BoundingBox;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}
```

### DamageArea Interface

```typescript
interface DamageArea {
  id: string;
  mediaId: string;
  location: 'front' | 'rear' | 'driver_side' | 'passenger_side' | 'roof' | 'hood' | 'trunk';
  damageType: 'dent' | 'scratch' | 'crack' | 'shattered' | 'crushed' | 'missing_part';
  severity: 'minor' | 'moderate' | 'severe' | 'total_loss';
  components: string[];
  description: string;
  confidence: number;
  boundingBox?: BoundingBox;
  estimatedRepairMin?: number;
  estimatedRepairMax?: number;
  adjusterConfirmed?: boolean;
  adjusterSeverityOverride?: string;
  adjusterNotes?: string;
}
```

### RepairItem Interface

```typescript
interface RepairItem {
  id: string;
  mediaId: string;
  lineNumber: number;
  itemType: 'parts' | 'labor' | 'paint' | 'materials' | 'sublet' | 'other';
  description: string;
  partNumber?: string;
  oemPart?: boolean;
  quantity: number;
  unitPrice?: number;
  totalPrice: number;
  laborHours?: number;
  laborRate?: number;
  laborType?: string;
  aiValidated: boolean;
  validationNotes?: string;
  marketRateComparison?: number;
}
```

### ClaimAssessment Interface

```typescript
interface ClaimAssessment {
  id: string;
  applicationId: string;
  // Overall
  severityRating: 'Low' | 'Medium' | 'High' | 'Critical';
  severityRationale: string;
  // Liability
  liabilityDetermination?: string;
  insuredLiabilityPercentage?: number;
  liabilityRationale?: string;
  liabilityEvidence?: EvidenceReference[];
  // Damage
  overallDamageSeverity?: string;
  totalDamageAreas: number;
  affectedComponents: string[];
  // Financial
  totalRepairEstimate?: number;
  aiValidatedEstimate?: number;
  estimateVariancePercentage?: number;
  // Payout
  payoutMin?: number;
  payoutMax?: number;
  payoutRecommended?: number;
  payoutRationale?: string;
  // Policies
  policiesApplied: PolicyApplication[];
  // Fraud
  fraudRiskLevel?: 'Low' | 'Medium' | 'High';
  fraudIndicators?: FraudIndicator[];
  siuReferralRecommended: boolean;
  // Adjuster
  adjusterDecision?: string;
  adjusterDecisionDate?: string;
  adjusterNotes?: string;
  adjusterOverrideAmount?: number;
  createdAt: string;
  updatedAt: string;
}

interface PolicyApplication {
  policyId: string;
  criteriaId: string;
  action: string;
  impact: string;
}

interface FraudIndicator {
  indicator: string;
  severity: 'Low' | 'Medium' | 'High';
  description: string;
}

interface EvidenceReference {
  mediaId: string;
  mediaType: string;
  description: string;
}
```

---

## Migration Scripts

### Migration 006: Create Automotive Claims Tables

```sql
-- migrations/006_create_automotive_claims_tables.sql

-- Enable extensions (if not already)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Use workbenchiq schema
SET search_path TO workbenchiq, public;

-- 1. claim_media table
CREATE TABLE IF NOT EXISTS claim_media (
    -- ... (full definition above)
);

-- 2. claim_keyframes table
CREATE TABLE IF NOT EXISTS claim_keyframes (
    -- ... (full definition above)
);

-- 3. claim_damage_areas table
CREATE TABLE IF NOT EXISTS claim_damage_areas (
    -- ... (full definition above)
);

-- 4. claim_repair_items table
CREATE TABLE IF NOT EXISTS claim_repair_items (
    -- ... (full definition above)
);

-- 5. claim_policy_chunks table
CREATE TABLE IF NOT EXISTS claim_policy_chunks (
    -- ... (full definition above)
);

-- 6. claim_assessments table
CREATE TABLE IF NOT EXISTS claim_assessments (
    -- ... (full definition above)
);
```

---

## Relationships

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────────┐
│  applications   │◄────┤│   claim_media   │◄─────│  claim_keyframes    │
│  (existing)     │  1:N │                 │  1:N │  (video only)       │
└─────────────────┘      └─────────────────┘      └─────────────────────┘
        │                        │
        │                        │ 1:N
        │                        ▼
        │                ┌─────────────────┐
        │                │claim_damage_areas│
        │                │  (image only)   │
        │                └─────────────────┘
        │                        │
        │                        │ 1:N
        │                        ▼
        │                ┌─────────────────┐
        │                │claim_repair_items│
        │                │  (document only) │
        │                └─────────────────┘
        │
        │ 1:1
        ▼
┌─────────────────┐
│claim_assessments│
│ (AI assessment) │
└─────────────────┘

┌─────────────────────┐
│ claim_policy_chunks │  (Standalone - for RAG)
│ (automotive policies)│
└─────────────────────┘
```

---

## Index Strategy

### Query Patterns and Indexes

| Query Pattern | Table | Index |
|--------------|-------|-------|
| Get all media for a claim | claim_media | `idx_claim_media_application` |
| Filter by media type | claim_media | `idx_claim_media_type` |
| Find processing errors | claim_media | `idx_claim_media_status` |
| Get keyframes for video | claim_keyframes | `idx_keyframes_media` |
| Find impact frames | claim_keyframes | `idx_keyframes_impact` |
| Get damage by location | claim_damage_areas | `idx_damage_location` |
| Filter by severity | claim_damage_areas | `idx_damage_severity` |
| Vector search on policies | claim_policy_chunks | `idx_claim_policy_chunks_embedding` (HNSW) |
| Hybrid text search | claim_policy_chunks | `idx_claim_policy_chunks_content_trgm` |
