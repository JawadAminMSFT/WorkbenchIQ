# Quickstart: Canadian Mortgage Underwriting Persona

**Feature**: 008-mortgage-underwriting  
**Date**: 2026-01-22

---

## One-Command Setup (Recommended)

Run the automated setup script to configure everything:

```powershell
# From project root directory
.\scripts\setup_mortgage_underwriting.ps1 -StartServers
```

This script will:
- ✅ Validate your environment (Python, Node.js, .env)
- ✅ Install Python dependencies
- ✅ Create package structure (`app/mortgage/`)
- ✅ Update persona registry and unified indexer config
- ✅ Create Azure Content Understanding mortgage analyzer
- ✅ Create mortgage underwriting policies file
- ✅ Index policies for RAG (PostgreSQL + pgvector)
- ✅ Install frontend dependencies
- ✅ Start API and frontend servers
- ✅ Open browser to http://localhost:3000

### Script Options

```powershell
# Full setup and start servers
.\scripts\setup_mortgage_underwriting.ps1 -StartServers

# Skip Azure analyzer setup (if already configured)
.\scripts\setup_mortgage_underwriting.ps1 -SkipAzureSetup -StartServers

# Verify environment without making changes
.\scripts\setup_mortgage_underwriting.ps1 -VerifyOnly

# Setup only, don't start servers
.\scripts\setup_mortgage_underwriting.ps1

# Re-index policies only
.\scripts\setup_mortgage_underwriting.ps1 -IndexPoliciesOnly
```

---

## Prerequisites

Before running the setup script, ensure you have:

1. **Azure Subscription** with Content Understanding resource
2. **Azure OpenAI** deployment with `text-embedding-3-small` model
3. **Azure PostgreSQL** with pgvector extension enabled
4. **Python 3.11+** and **Node.js 18+** installed
5. **`.env` file** with required settings (copy from `.env.example`)

### Required Environment Variables

```bash
# Azure Content Understanding
AZURE_CONTENT_UNDERSTANDING_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_CONTENT_UNDERSTANDING_API_KEY=your-api-key

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# PostgreSQL (for policy RAG)
POSTGRES_HOST=your-postgres.postgres.database.azure.com
POSTGRES_DB=workbenchiq
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password

# Mortgage Underwriting (optional - has defaults)
MORTGAGE_UNDERWRITING_ENABLED=true
MORTGAGE_DOC_ANALYZER=mortgageDocAnalyzer
MORTGAGE_POLICIES_PATH=prompts/mortgage-underwriting-policies.json
OSFI_MQR_FLOOR_PCT=5.25
OSFI_MQR_BUFFER_PCT=2.0
GDS_LIMIT_STANDARD=0.39
TDS_LIMIT_STANDARD=0.44
```

---

## Manual Setup Steps

If you prefer manual setup or the script fails, follow these steps:

### 1. Install Dependencies

```powershell
# Python dependencies
uv sync
# or: pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Create Package Structure

```powershell
# From repository root
mkdir app\mortgage
mkdir app\mortgage\extractors
mkdir app\mortgage\risk
```

Create `app/mortgage/__init__.py`:

```python
"""
Canadian Mortgage Underwriting Module

This module provides mortgage underwriting capabilities including:
- Document processing and field extraction
- GDS/TDS/LTV calculations with OSFI stress testing
- Policy-based application evaluation
- Risk signal detection
"""

from .engine import MortgagePolicyEngine
from .calculator import MortgageCalculator
from .policies import MortgagePolicyLoader

__all__ = [
    "MortgagePolicyEngine",
    "MortgageCalculator", 
    "MortgagePolicyLoader",
]
```

### 3. Add Configuration

Add to `app/config.py`:

```python
@dataclass
class MortgageUnderwritingSettings:
    """Settings for mortgage underwriting persona."""
    
    enabled: bool = True
    doc_analyzer: str = "mortgageDocAnalyzer"
    policies_path: str = "prompts/mortgage-underwriting-policies.json"
    osfi_mqr_floor_pct: float = 5.25
    osfi_mqr_buffer_pct: float = 2.0
    gds_limit_standard: float = 0.39
    tds_limit_standard: float = 0.44
    
    @classmethod
    def from_env(cls) -> "MortgageUnderwritingSettings":
        return cls(
            enabled=os.getenv("MORTGAGE_UNDERWRITING_ENABLED", "true").lower() == "true",
            doc_analyzer=os.getenv("MORTGAGE_DOC_ANALYZER", "mortgageDocAnalyzer"),
            policies_path=os.getenv("MORTGAGE_POLICIES_PATH", "prompts/mortgage-underwriting-policies.json"),
            osfi_mqr_floor_pct=float(os.getenv("OSFI_MQR_FLOOR_PCT", "5.25")),
            osfi_mqr_buffer_pct=float(os.getenv("OSFI_MQR_BUFFER_PCT", "2.0")),
            gds_limit_standard=float(os.getenv("GDS_LIMIT_STANDARD", "0.39")),
            tds_limit_standard=float(os.getenv("TDS_LIMIT_STANDARD", "0.44")),
        )
```

### 4. Update Persona Registry

Add to `app/personas.py`:

```python
# Add to PersonaType enum
MORTGAGE_UNDERWRITING = "mortgage_underwriting"

# Add to PERSONA_CONFIGS dict
PersonaType.MORTGAGE_UNDERWRITING: PersonaConfig(
    id="mortgage_underwriting",
    name="Mortgage Underwriting",
    description="Canadian residential mortgage underwriting workbench with OSFI B-20 compliance",
    icon="🏠",
    color="#059669",  # Emerald
    field_schema=MORTGAGE_UNDERWRITING_FIELD_SCHEMA,
    default_prompts=MORTGAGE_UNDERWRITING_DEFAULT_PROMPTS,
    custom_analyzer_id="mortgageDocAnalyzer",
    enabled=True,
),
```

### 5. Update Unified Indexer

Add to `app/rag/unified_indexer.py` in `PERSONA_CONFIG`:

```python
"mortgage_underwriting": {
    "policies_path": "prompts/mortgage-underwriting-policies.json",
    "table_name": "mortgage_policy_chunks",
    "display_name": "Mortgage Underwriting",
},
```

### 6. Create Azure Analyzer

```powershell
python scripts/setup_mortgage_analyzers.py --create-all
python scripts/setup_mortgage_analyzers.py --verify
```

### 7. Create Policies File

Create `prompts/mortgage-underwriting-policies.json` (see full content below)

### 8. Index Policies

```powershell
python scripts/index_mortgage_policies.py
```

### 9. Start Servers

```powershell
# Option A: Use the launcher script
.\scripts\run_frontend.bat

# Option B: Start manually in separate terminals
# Terminal 1 - API
uv run python -m uvicorn api_server:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 10. Open Browser

- **Frontend**: http://localhost:3000
- **Admin View**: http://localhost:3000/admin  
- **API Docs**: http://localhost:8000/docs

---

## Database Tables

The `mortgage_policy_chunks` table is created automatically by the unified indexer.
No manual migration is needed - the indexer uses `CREATE TABLE IF NOT EXISTS`.

### Verify Table (Optional)

```sql
-- Connect to PostgreSQL and run:
SELECT COUNT(*) FROM workbenchiq.mortgage_policy_chunks;
```

---

## UI Testing Workflow

Once servers are running:

### 1. Admin View - Create & Upload

1. Navigate to **http://localhost:3000/admin**
2. Select **"Mortgage Underwriting"** 🏠 from persona dropdown
3. Click **"Create Application"**
4. Upload mortgage documents (T4, pay stubs, application form, appraisal)
5. Click **"Process"** to run document extraction

### 2. Mortgage Underwriter View - Review

1. Click on application to open 3-column workbench
2. **Left Column**: Evidence browser with document viewer
3. **Middle Column**: Case summary with GDS/TDS/LTV calculations
4. **Right Column**: Policy findings with exception handling
5. Make underwriter decision: Approve / Decline / Refer

### 3. Ask IQ - Policy Questions

Try questions like:
- "What is the OSFI stress test rate for uninsured mortgages?"
- "What are the GDS and TDS limits?"
- "When should I decline a conventional mortgage?"
- "What income types require a 2-year average?"

---

## Policies File Content

Create `prompts/mortgage-underwriting-policies.json`:

```json
{
  "version": "1.0",
  "jurisdiction": "CA",
  "effective_date": "2026-01-01",
  "description": "Canadian Mortgage Underwriting Policies - OSFI B-20 Aligned",
  "policies": [
    {
      "id": "CA.OSFI.MQR.UNINSURED",
      "category": "osfi_regulatory",
      "subcategory": "stress_test",
      "name": "Uninsured Mortgage Qualifying Rate (MQR)",
      "description": "OSFI requires uninsured mortgages to be qualified at the greater of contract rate + 2% or 5.25% floor",
      "criteria": [
        {
          "id": "CA.OSFI.MQR.UNINSURED-A",
          "condition": "product_type IN ('conventional', 'insurable') AND NOT insured",
          "action": "Apply qualifying rate = max(contract_rate + 2%, 5.25%)",
          "severity": "critical",
          "rationale": "OSFI mandates stress testing to ensure borrowers can handle rate increases"
        }
      ]
    },
    {
      "id": "CA.UW.DSR.GDS_LIMIT",
      "category": "income_qualification",
      "subcategory": "debt_service",
      "name": "GDS Limit at Stress Test Rate",
      "description": "GDS at qualifying rate should not exceed lender limit",
      "criteria": [
        {
          "id": "CA.UW.DSR.GDS_LIMIT-A",
          "condition": "stress_test_gds <= 0.39",
          "status": "pass"
        },
        {
          "id": "CA.UW.DSR.GDS_LIMIT-B",
          "condition": "stress_test_gds > 0.39 AND stress_test_gds <= 0.42",
          "status": "needs_review",
          "action": "Document compensating factors"
        },
        {
          "id": "CA.UW.DSR.GDS_LIMIT-C",
          "condition": "stress_test_gds > 0.42",
          "status": "exception_required",
          "action": "Senior underwriter approval required"
        }
      ]
    },
    {
      "id": "CA.UW.DSR.TDS_LIMIT",
      "category": "income_qualification",
      "subcategory": "debt_service",
      "name": "TDS Limit at Stress Test Rate",
      "description": "TDS at qualifying rate should not exceed lender limit",
      "criteria": [
        {
          "id": "CA.UW.DSR.TDS_LIMIT-A",
          "condition": "stress_test_tds <= 0.44",
          "status": "pass"
        },
        {
          "id": "CA.UW.DSR.TDS_LIMIT-B",
          "condition": "stress_test_tds > 0.44 AND stress_test_tds <= 0.47",
          "status": "needs_review"
        },
        {
          "id": "CA.UW.DSR.TDS_LIMIT-C",
          "condition": "stress_test_tds > 0.47",
          "status": "exception_required"
        }
      ]
    },
    {
      "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL",
      "category": "collateral_valuation",
      "subcategory": "ltv_limits",
      "name": "Conventional Mortgage LTV Limits",
      "description": "Conventional mortgages must have LTV <= 80%",
      "criteria": [
        {
          "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL-A",
          "condition": "product_type = 'conventional' AND ltv <= 0.80",
          "status": "pass"
        },
        {
          "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL-B",
          "condition": "product_type = 'conventional' AND ltv > 0.80",
          "status": "fail",
          "action": "Mortgage insurance required or reduce loan amount"
        }
      ]
    }
  ]
}
```

---

## API Endpoints Reference

```bash
# Mortgage Applications (uses unified application API)
POST /api/applications                    # Create new mortgage case
GET  /api/applications/{id}               # Get case with mortgage_case data
POST /api/applications/{id}/upload        # Upload documents
POST /api/applications/{id}/process       # Extract fields from documents

# Mortgage-Specific Endpoints
GET  /api/mortgage/{id}/calculations      # Get GDS/TDS/LTV calculations
POST /api/mortgage/{id}/evaluate          # Run policy evaluation
GET  /api/mortgage/{id}/findings          # Get policy findings
POST /api/mortgage/{id}/decision          # Submit underwriter decision

# Ask IQ (RAG)
POST /api/chat                            # Chat with persona=mortgage_underwriting
```

Full API docs: http://localhost:8000/docs

---

## Running Tests

```powershell
# All mortgage underwriting tests
pytest tests/test_mortgage_*.py -v

# Specific phase
pytest tests/test_mortgage_phase1_config.py -v
pytest tests/test_mortgage_phase5_calculator.py -v
pytest tests/test_mortgage_phase6_policy_engine.py -v

# With coverage
pytest tests/test_mortgage_*.py --cov=app/mortgage --cov-report=html
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Analyzer not found" | `python scripts/setup_mortgage_analyzers.py --create-all` |
| "No policy results" | `python scripts/index_mortgage_policies.py` |
| "Database connection error" | Check PostgreSQL settings in `.env` |
| "Port already in use" | Kill existing processes on 8000/3000 |
| "GDS/TDS mismatch" | Verify inputs are monthly, check condo fee handling |
| "MQR not applied" | Check `productType` is 'conventional' or 'insurable' |
| "Persona not in dropdown" | Verify `MORTGAGE_UNDERWRITING_ENABLED=true` in `.env` |

---

## Quick Reference

```powershell
# Full setup + start
.\scripts\setup_mortgage_underwriting.ps1 -StartServers

# Just start servers
.\scripts\run_frontend.bat

# Re-index policies
python scripts/index_mortgage_policies.py

# Run all tests
pytest tests/test_mortgage_*.py -v

# Verify analyzer
python scripts/setup_mortgage_analyzers.py --verify
```

---

## Sample Test Case

Use the sample data from `mortgage-research/canadian_mortgage_sample_package/bundle_ground_truth.json`:

```json
{
  "deal": {
    "purchase_price": 850000,
    "down_payment": 170000,
    "requested_loan_amount": 680000,
    "contract_rate_pct": 5.25
  },
  "derived_metrics": {
    "ltv_estimate": 0.8,
    "gds_estimate": 0.2657,
    "tds_estimate": 0.2886
  }
}
```

Expected calculations:
- LTV = 680,000 / 850,000 = **80%** ✓
- Qualifying rate = max(5.25 + 2, 5.25) = **7.25%**
- Contract GDS ≈ **26.6%** ✓
- Contract TDS ≈ **28.9%** ✓

---

## Next Steps

After completing this quickstart:

1. Review [spec.md](spec.md) for full requirements
2. Follow [tasks.md](tasks.md) for implementation checklist
3. Reference [data-model.md](data-model.md) for JSON storage schema
4. Use [research.md](research.md) for OSFI calculation formulas
