# Data Model: Canadian Mortgage Underwriting Persona

**Feature**: 008-mortgage-underwriting  
**Date**: 2026-01-22  
**Status**: Draft

---

## Overview

This document details the data model for the Canadian mortgage underwriting persona, following the **unified storage pattern** established in the codebase:

| Data Type | Storage | Location |
|-----------|---------|----------|
| **Applications/Cases** | JSON files | `data/applications/{id}/metadata.json` |
| **Extracted content** | JSON files | `data/applications/{id}/content_understanding.json` |
| **Conversations** | JSON files | `data/applications/{id}/chats/{chat_id}.json` |
| **Policy chunks (RAG)** | PostgreSQL + pgvector | `mortgage_policy_chunks` table |

This is consistent with how other personas (underwriting, automotive_claims, life_health_claims) store data.

### Design Principles

1. **JSON for application data** - Full mortgage case details stored in `metadata.json`
2. **Single PostgreSQL table for policies** - `mortgage_policy_chunks` for RAG vector search
3. **Leverage existing infrastructure** - Uses `ApplicationMetadata`, `StoredFile` dataclasses
4. **Schema compliance** - JSON structure follows `canada_mortgage_case.schema.json`

---

## Storage Architecture

```
data/
├── applications/
│   └── {mortgage_case_id}/              # Unique case ID (UUID or mtg-XXXXXX)
│       ├── metadata.json                 # Full case data + status + persona
│       ├── content_understanding.json    # Azure CU extraction results
│       ├── files/                        # Uploaded documents
│       │   ├── application_form.pdf
│       │   ├── t4_primary.pdf
│       │   ├── paystub_01.pdf
│       │   └── appraisal.pdf
│       └── chats/                        # Conversation history
│           ├── {chat_id_1}.json
│           └── {chat_id_2}.json
└── conversations/                        # (Legacy fallback location)

PostgreSQL (workbenchiq schema):
└── mortgage_policy_chunks               # RAG vector search table
```

---

## JSON Schema: metadata.json

The `metadata.json` file extends `ApplicationMetadata` with mortgage-specific data.

### Base Structure (from app/storage.py)

```jsonc
{
  // Standard ApplicationMetadata fields
  "id": "mtg-a1b2c3d4",
  "created_at": "2026-01-22T14:30:00Z",
  "external_reference": "MTG-2026-001",
  "status": "in_review",
  "persona": "mortgage_underwriting",
  "files": [
    {
      "filename": "application_form.pdf",
      "path": "data/applications/mtg-a1b2c3d4/files/application_form.pdf",
      "content_type": "application/pdf",
      "media_type": "document"
    }
  ],
  "processing_status": "completed",
  "analyzer_id_used": "mortgage-doc-analyzer",
  
  // Mortgage-specific extension
  "mortgage_case": {
    // Full case data per canada_mortgage_case.schema.json
  },
  
  // Risk analysis results
  "risk_analysis": {
    "findings": [],
    "risk_score": null,
    "recommendation": null
  },
  
  // LLM outputs (underwriter assistant responses)
  "llm_outputs": {}
}
```

### mortgage_case Structure

The `mortgage_case` object follows the canonical schema from `canada_mortgage_case.schema.json`:

```jsonc
{
  "mortgage_case": {
    "caseId": "mtg-a1b2c3d4",
    "status": "in_review",
    "province": "ON",
    "channel": "broker",
    "lenderId": "ABC-BANK",
    "timestamps": {
      "submittedAt": "2026-01-22T14:30:00Z",
      "lastUpdatedAt": "2026-01-22T15:45:00Z"
    },
    
    "application": {
      "purpose": "purchase",
      "requestedAmount": 520000,
      "amortizationYears": 25,
      "productType": "fixed_closed",
      "termYears": 5,
      "occupancy": "owner_occupied",
      "insurer": "cmhc",
      "insurancePremiumPct": 2.8
    },
    
    "property": {
      "address": {
        "streetAddress": "123 Maple Street",
        "city": "Toronto",
        "province": "ON",
        "postalCode": "M5V 1A1"
      },
      "propertyType": "condo",
      "purchasePrice": 650000,
      "appraisedValue": 660000,
      "annualPropertyTaxes": 5040,
      "monthlyCondoFees": 650,
      "heatingMonthly": 80
    },
    
    "borrowers": [
      {
        "borrowerId": "B1",
        "role": "primary",
        "identity": {
          "fullName": "Jane Smith",
          "dateOfBirth": "1988-03-15",
          "sin": "***-***-789",
          "maritalStatus": "single",
          "dependents": 0
        },
        "residency": {
          "status": "citizen",
          "sinceDate": "1988-03-15",
          "countryOfCitizenship": "CA"
        },
        "employment": [
          {
            "type": "primary",
            "employerName": "TechCorp Inc",
            "positionTitle": "Senior Developer",
            "startDate": "2020-06-01",
            "employmentStatus": "full_time",
            "verified": true
          }
        ],
        "income": [
          {
            "incomeType": "salary",
            "amount": 125000,
            "frequency": "annual",
            "qualifyingAmountMonthly": 10416.67,
            "verification": {
              "method": "t4_paystub",
              "documentIds": ["t4_B1", "paystub_B1_1"],
              "verifiedAmount": 125000
            }
          }
        ],
        "assets": [
          {
            "assetType": "savings",
            "institution": "TD Bank",
            "value": 180000,
            "liquid": true,
            "sourceOfFunds": "savings"
          }
        ],
        "liabilities": [
          {
            "liabilityType": "credit_card",
            "lender": "VISA",
            "balance": 5000,
            "paymentMonthly": 150,
            "isJoint": false
          }
        ],
        "creditProfile": {
          "bureauScore": 742,
          "bureauAgency": "equifax",
          "reportDate": "2026-01-20",
          "delinquencies": [],
          "inquiriesLast6Months": 2,
          "utilizationPercent": 15
        }
      }
    ],
    
    "calculations": {
      "gds": {
        "value": 31.2,
        "limit": 32.0,
        "status": "pass",
        "inputs": {
          "mortgagePaymentMonthly": 2456.78,
          "propertyTaxesMonthly": 420.00,
          "heatingMonthly": 80.00,
          "condoFeesMonthly": 325.00,
          "grossIncomeMonthly": 10416.67
        },
        "stressTestRate": 5.25
      },
      "tds": {
        "value": 38.5,
        "limit": 40.0,
        "status": "pass",
        "inputs": {
          "gdsAmount": 3281.78,
          "otherDebtsMonthly": 450.00,
          "grossIncomeMonthly": 10416.67
        }
      },
      "ltv": {
        "value": 80.0,
        "limit": 95.0,
        "status": "pass",
        "loanAmount": 520000,
        "propertyValue": 650000
      },
      "mqr": {
        "contractRate": 4.79,
        "stressTestRate": 5.25,
        "method": "floor",
        "note": "Max of contract+2% (6.79%) or floor (5.25%)"
      }
    },
    
    "documents": [
      {
        "documentId": "t4_B1",
        "documentType": "t4",
        "borrowerId": "B1",
        "fileName": "t4_primary.pdf",
        "pages": 1,
        "receivedAt": "2026-01-22T14:35:00Z",
        "classification": {
          "label": "t4",
          "confidence": 0.97
        }
      }
    ],
    
    "policyFindings": [
      {
        "findingId": "F001",
        "ruleId": "OSFI-B20-GDS",
        "ruleName": "GDS Ratio Limit",
        "status": "pass",
        "severity": "info",
        "message": "GDS ratio 31.2% within limit of 32%",
        "evidence": [
          {
            "documentId": "t4_B1",
            "page": 1,
            "field": "income.qualifyingAmountMonthly"
          }
        ]
      }
    ],
    
    "decision": null
  }
}
```

---

## content_understanding.json

Raw extraction results from Azure Content Understanding:

```jsonc
{
  "analyzer_id": "mortgage-doc-analyzer",
  "processed_at": "2026-01-22T15:00:00Z",
  "documents": [
    {
      "document_id": "t4_B1",
      "file_name": "t4_primary.pdf",
      "extraction_result": {
        "fields": {
          "EmployerName": {
            "value": "TechCorp Inc",
            "confidence": 0.95,
            "boundingRegion": {"page": 1, "polygon": [...]},
            "sourceText": "Box 54: TechCorp Inc"
          },
          "Box14_EmploymentIncome": {
            "value": 125000.00,
            "confidence": 0.98,
            "boundingRegion": {"page": 1, "polygon": [...]},
            "sourceText": "125,000.00"
          }
        }
      }
    }
  ]
}
```

---

## Conversation Storage: chats/{chat_id}.json

```jsonc
{
  "chat_id": "chat-xyz123",
  "case_id": "mtg-a1b2c3d4",
  "persona": "mortgage_underwriting",
  "created_at": "2026-01-22T16:00:00Z",
  "updated_at": "2026-01-22T16:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "What is the stress test rate for this application?",
      "timestamp": "2026-01-22T16:00:00Z"
    },
    {
      "role": "assistant",
      "content": "The stress test rate for this application is **5.25%** (the OSFI floor rate). This is because the contract rate of 4.79% + 2% = 6.79% exceeds the floor, so the floor applies.",
      "timestamp": "2026-01-22T16:00:05Z",
      "sources": [
        {"type": "policy", "id": "OSFI-B20-MQR", "chunk_id": "..."}
      ]
    }
  ]
}
```

---

## PostgreSQL: mortgage_policy_chunks (RAG Only)

The **only PostgreSQL table** for this persona is the policy chunks table for vector search.
This follows the unified indexer pattern from `app/rag/unified_indexer.py`.

### Table Schema

```sql
CREATE TABLE workbenchiq.mortgage_policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    
    -- Chunk metadata
    chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
        'policy_header', 'criteria', 'modifying_factor', 'reference', 'description'
    )),
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    
    -- Categorization
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    
    -- Rule details
    criteria_id VARCHAR(50),
    risk_level VARCHAR(30),
    action_recommendation TEXT,
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    
    -- Embedding
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index for upsert
CREATE UNIQUE INDEX idx_mortgage_policy_chunks_unique ON workbenchiq.mortgage_policy_chunks 
    (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

-- HNSW index for vector search
CREATE INDEX idx_mortgage_policy_chunks_embedding ON workbenchiq.mortgage_policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Filtering indexes
CREATE INDEX idx_mortgage_policy_chunks_category ON workbenchiq.mortgage_policy_chunks (category);
CREATE INDEX idx_mortgage_policy_chunks_subcategory ON workbenchiq.mortgage_policy_chunks (subcategory);
```

### Unified Indexer Integration

Add to `PERSONA_CONFIG` in `app/rag/unified_indexer.py`:

```python
PERSONA_CONFIG = {
    # ... existing personas ...
    "mortgage_underwriting": {
        "policies_path": "prompts/mortgage-underwriting-policies.json",
        "table_name": "mortgage_policy_chunks",
        "display_name": "Mortgage Underwriting",
    },
}
```

---

## Application Data in JSON

All mortgage case data is stored in JSON files using the existing `ApplicationMetadata` infrastructure.

### Key Differences from PostgreSQL Approach

| Aspect | JSON Storage (Correct) | PostgreSQL (Not Used) |
|--------|------------------------|------------------------|
| Case data | `metadata.json` | ~~mortgage_cases table~~ |
| Borrower data | Embedded in `metadata.json` | ~~mortgage_borrowers table~~ |
| Document metadata | `metadata.json` + `content_understanding.json` | ~~mortgage_docs table~~ |
| Field extractions | `content_understanding.json` | ~~field_extractions table~~ |
| Calculations | `metadata.json → mortgage_case.calculations` | ~~mortgage_calculations table~~ |
| Policy findings | `metadata.json → risk_analysis.findings` | ~~mortgage_policy_findings table~~ |
| Decisions | `metadata.json → mortgage_case.decision` | ~~mortgage_decisions table~~ |

### Benefits of JSON Storage

1. **Consistency** - Same pattern as all other personas
2. **Simplicity** - No additional database migrations
3. **Flexibility** - Easy schema evolution without migrations
4. **Portability** - Cases can be exported/imported as files
5. **Proven** - Works well for existing underwriting and claims personas

---

## Storage Provider Integration

Uses existing storage provider infrastructure from `app/storage_providers/`:

```python
# Local storage
data/applications/{case_id}/metadata.json
data/applications/{case_id}/content_understanding.json
data/applications/{case_id}/files/*.pdf

# Azure Blob storage (when configured)
{container}/{case_id}/metadata.json
{container}/{case_id}/content_understanding.json
{container}/{case_id}/files/*.pdf
```

### Loading Cases by Persona

```python
from app.storage import list_applications, load_application

# List all mortgage cases
mortgage_cases = list_applications(persona_filter="mortgage_underwriting")

# Load specific case
case = load_application("mtg-a1b2c3d4")
mortgage_data = case.get("mortgage_case", {})
```

---

## Data Lifecycle

### Case Status Flow (in metadata.json)

```
┌─────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐
│ intake  │───▶│ in_review │───▶│ pending_info │───▶│ approved │
└─────────┘    └───────────┘    └──────────────┘    └──────────┘
                    │                                     │
                    ▼                                     ▼
               ┌──────────┐                          ┌────────┐
               │ declined │                          │ funded │
               └──────────┘                          └────────┘
                    │
                    ▼
               ┌──────────┐
               │ referred │ ◀─── (exception review)
               └──────────┘
```

### Processing Status (in metadata.json)

```
idle ──▶ extracting ──▶ analyzing ──▶ completed
              │              │
              ▼              ▼
           error          error
```

---

## Migration Script

Only one table is created in PostgreSQL:

```sql
-- Migration: 012_create_mortgage_policy_chunks.sql
-- Description: Create mortgage policy chunks table for RAG
-- Author: WorkbenchIQ
-- Date: 2026-01-22

BEGIN;

-- Ensure schema exists
CREATE SCHEMA IF NOT EXISTS workbenchiq;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create mortgage_policy_chunks table (only PostgreSQL table for this persona)
CREATE TABLE IF NOT EXISTS workbenchiq.mortgage_policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    policy_name VARCHAR(200) NOT NULL,
    chunk_type VARCHAR(30) NOT NULL CHECK (chunk_type IN (
        'policy_header', 'criteria', 'modifying_factor', 'reference', 'description'
    )),
    chunk_sequence INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    criteria_id VARCHAR(50),
    risk_level VARCHAR(30),
    action_recommendation TEXT,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(1536) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_mortgage_policy_chunks_unique 
    ON workbenchiq.mortgage_policy_chunks 
    (policy_id, chunk_type, COALESCE(criteria_id, ''), content_hash);

CREATE INDEX IF NOT EXISTS idx_mortgage_policy_chunks_embedding 
    ON workbenchiq.mortgage_policy_chunks 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_mortgage_policy_chunks_category 
    ON workbenchiq.mortgage_policy_chunks (category);

CREATE INDEX IF NOT EXISTS idx_mortgage_policy_chunks_subcategory 
    ON workbenchiq.mortgage_policy_chunks (subcategory);

COMMIT;
```

---

## References

- [canada_mortgage_case.schema.json](../../../mortgage-research/canada_mortgage_case.schema.json) - Full canonical schema
- [canada_underwriting_rules_catalog.yaml](../../../mortgage-research/canada_underwriting_rules_catalog.yaml) - Policy rules
- [unified_indexer.py](../../../app/rag/unified_indexer.py) - Pattern for policy chunk tables
- [app/storage.py](../../../app/storage.py) - ApplicationMetadata dataclass
- [app/storage_providers/](../../../app/storage_providers/) - Local and Azure storage providers
