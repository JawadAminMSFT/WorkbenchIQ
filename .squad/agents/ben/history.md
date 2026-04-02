# Ben — History

## Project Context

underwriting-assistant backend is a Python FastAPI application. Uses Azure OpenAI for LLM-powered document analysis. Key modules include document processing, scoring engine, mortgage analysis, and API server. Background processing uses status tracking (extracting/analyzing/error).

## Learnings

### 2025-01-XX: Wired Backend Engines into API Router

**Task:** Wire 4 backend engines (QuoteExtractor, PlacementEngine, ClientResearchEngine, BrokerStorage) into the API router at `app/broker/api.py`.

**Key Files:**
- `app/broker/api.py` — Main API router with endpoints
- `app/broker/quote_extractor.py` — QuoteExtractor class for LLM-powered quote field extraction
- `app/broker/placement_engine.py` — PlacementEngine for scoring and ranking quotes
- `app/broker/research_engine.py` — ClientResearchEngine for AI-powered client research
- `app/broker/storage.py` — BrokerStorage for data persistence

**Implementations:**

1. **QuoteExtractor Integration** (Upload Quote Endpoint)
   - Wired into `POST /api/broker/submissions/{submission_id}/quotes`
   - After file upload, calls `QuoteExtractor.extract_quote()` to extract structured fields
   - Requires OpenAISettings from config
   - Updates quote status: RAW → EXTRACTED (or stays RAW if extraction fails)
   - Graceful fallback: if extraction fails, quote is still saved but status remains RAW

2. **PlacementEngine Integration** (Compare Quotes Endpoint)
   - Wired into `POST /api/broker/submissions/{submission_id}/compare`
   - Loads carrier profiles using `storage.get_carrier_profile_by_name()`
   - Converts dict data to dataclass instances (Quote, Submission, CarrierProfile)
   - Calls `PlacementEngine.score_quotes()` to compute placement scores
   - Calls `PlacementEngine.generate_recommendation()` for top-ranked quote
   - Saves scored quotes back to storage
   - Graceful fallback: if engine fails, returns basic comparison with manual review message

3. **ClientResearchEngine Integration** (Research Client Endpoint)
   - Wired into `POST /api/broker/clients/{client_id}/research`
   - Calls `ClientResearchEngine.research_client()` for AI-powered research
   - Saves research brief to client record (`client.research_brief`)
   - Formats structured research data into markdown brief for response
   - Graceful fallback: if research engine fails, returns basic client data from storage

4. **BrokerStorage Enhancement**
   - Added `get_carrier_profile_by_name()` method for case-insensitive carrier lookup
   - Used by PlacementEngine to load carrier profiles for FSR scoring

**Patterns & Conventions:**
- All engines require `OpenAISettings` from `load_settings()`
- API endpoints convert between dict (storage) ↔ dataclass (engine) representations
- Graceful degradation: engines wrapped in try/except, API stays functional even if AI features fail
- Status tracking: quotes go through RAW → EXTRACTED lifecycle
- Async/await pattern: engines use `async def` and `await` for non-blocking LLM calls

**Error Handling:**
- Engine failures logged but don't crash the API
- Partial success: e.g., quote uploaded even if extraction fails
- Fallback responses: mock/basic data returned if AI engines unavailable

### 2026-03-25: Created Broker Data Seed Script

**Task:** Create `scripts/seed_broker_data.py` to populate demo data matching Commercial Brokerage spec.

**Key Files:**
- `scripts/seed_broker_data.py` — Standalone seed script for realistic demo data
- `data/broker/clients/*.json` — Client records
- `data/broker/submissions/*.json` — Submission records with embedded quotes
- `data/broker/carriers/*.json` — Carrier profile records

**Implementation:**

**Data Seeded:**
1. **2 Clients:** Ridgeview Properties LLC (3 locations, property rental) and Meridian Manufacturing Inc (1 location, machine shop)
2. **1 Submission:** For Ridgeview with pre-filled ACORD 125/140 fields, quoted status, 3 carriers
3. **3 Quotes:** AIG (rank #2, score 88.5), Zurich (rank #3, score 72.3 with gaps), Travelers (rank #1, score 93.2, premium)
4. **3 Carrier Profiles:** AIG (A+), Zurich (A+), Travelers (A++) with realistic financial data

**Patterns & Conventions:**
- **Fixed UUIDs:** Used deterministic UUIDs for idempotency (running script multiple times produces same data)
- **Quotes Embedded in Submissions:** Quotes stored as list within submission JSON (not separate files)
- **PlacementScoring Pre-calculated:** Each quote includes placement_score, placement_rank, coverage_adequacy, coverage_gaps
- **Realistic Data:** Premium amounts, TIVs, sublimits, financial ratios all realistic for commercial property market
- **Confidence Scores:** Lower confidence on fields with coverage gaps (e.g., Zurich flood_sublimit: 0.55)
- **Status Values:** Use constants from `app.broker.constants` (SubmissionStatus.QUOTED, QuoteStatus.EXTRACTED, etc.)

**Script Structure:**
- Uses `BrokerStorage` methods: `save_client()`, `save_submission()`, `save_carrier_profile()`
- Creates quotes as part of submission (embedded), not saved separately
- Imports from `app.broker.models`, `app.broker.constants`, `app.broker.storage`
- Returns helpful summary with placement rankings and file paths

**Key Learning:**
- Quotes are embedded in submissions' `quotes` list, not saved as separate entities
- Fixed UUIDs enable reproducible demo environments
- Pre-scored placement data allows frontend to display rankings without running engines

### 2026-03-25: Created Broker Sample Data for E2E Testing

**Task:** Create realistic input documents in `data/broker-sample-data/` for end-to-end pipeline testing through API and UI.

**Key Files:**
- `data/broker-sample-data/README.md` — Complete testing instructions with curl commands
- `data/broker-sample-data/ridgeview-sov.txt` — Statement of Values (3 properties, $18.5M TIV)
- `data/broker-sample-data/ridgeview-loss-runs.txt` — 5-year loss history (5 claims, $45,750 total)
- `data/broker-sample-data/ridgeview-prior-declaration.txt` — Current policy declaration page
- `data/broker-sample-data/quote-aig.txt` — AIG quote ($42,500 premium, $18.5M TIV)
- `data/broker-sample-data/quote-zurich.txt` — Zurich quote ($38,750 premium, $17M TIV, exclusions)
- `data/broker-sample-data/quote-travelers.txt` — Travelers quote ($47,200 premium, $19.5M TIV, highest coverage)
- `data/broker-sample-data/test-api.ps1` — PowerShell script for automated E2E testing

**Implementation:**

**Document Design:**
- All documents are plain text simulating PDF extraction output
- Formal professional formatting with headers, tables, aligned columns
- Every QuoteFields field is explicitly present and extractable by LLM
- Property values consistent across SOV and quote documents

**Client: Ridgeview Properties LLC**
- 3 commercial properties in Colorado (Denver, Aurora, Lakewood)
- Property types: Office (Fire Resistive), Warehouse (Masonry), Retail/Mixed-Use (Modified Fire Resistive)
- Total TIV: $18.5M (Building $11.8M + Contents $4.7M + BI $2.0M)
- Clean loss history: 5 minor claims over 5 years, all closed
- Years in business: 12, Annual revenue: $8.5M, 45 employees

**Quote Comparison Scenario:**
1. **AIG:** $42,500 premium, $18.5M TIV, $10K deductible, no exclusions, no conditions → Best balanced option
2. **Zurich:** $38,750 premium, $17M TIV (lower), $15K deductible, exclusions (mold, cyber), annual inspection required → Lowest price but coverage gaps
3. **Travelers:** $47,200 premium, $19.5M TIV (highest), $5K deductible (lowest), no exclusions, no conditions → Most comprehensive but highest cost

**Testing Workflow (README.md):**
- Step-by-step API calls with complete curl commands
- Client creation with 3 property_locations matching SOV values
- Submission creation for property line of business
- Quote uploads via multipart form data (carrier_name + file)
- Quote comparison endpoint to extract and score quotes
- Client research endpoint for AI-powered research
- Dashboard endpoint for metrics summary

**PowerShell Test Script (test-api.ps1):**
- Fully automated E2E test of entire pipeline
- Creates client with full property data
- Creates submission with coverage requirements
- Uploads all 3 carrier quote files using multipart form
- Runs comparison and displays results
- Attempts research and dashboard calls (graceful fallback if not implemented)
- Color-coded output with success/failure indicators
- Displays created resource IDs for further testing

**Key Patterns:**
- Documents are realistic but fictional (no real company data)
- All monetary values and property details align across documents
- Quote fields match exactly what `QuoteExtractor` extracts (annual_premium, deductibles, sublimits, exclusions, etc.)
- Property locations in client creation JSON match SOV document exactly
- Files are plain text (.txt) simulating PDF extraction, suitable for LLM processing
- Test script uses PowerShell `Invoke-RestMethod` with `-Form` parameter for multipart uploads

**Purpose:**
- These are **input documents** for testing document upload and extraction
- Different from seed data which creates pre-populated storage records
- Allows testing the full pipeline: upload → extract → score → compare → recommend
- Exercises both backend APIs and can be used through frontend UI

### 2026-03-25: Verified Broker API Endpoints and Seed Data

**Task:** Verify all broker API endpoints are properly registered and returning broker-specific data (not underwriting data) for the Commercial Brokerage persona fix.

**Verification Results:**

1. **Router Registration:** `app/broker/api.py` defines `APIRouter(prefix="/api/broker")`, mounted in `api_server.py` line 106 via `app.include_router(broker_api_router)`.

2. **Endpoints Confirmed Working:**
   - `GET /api/broker/dashboard` → Returns `DashboardMetrics` (total_accounts, open_submissions, bound_premium, renewals, stale)
   - `GET /api/broker/clients` → Returns list of broker `Client` records (Ridgeview Properties LLC, Meridian Manufacturing Inc)
   - `GET /api/broker/clients/{id}` → Individual client detail
   - `GET /api/broker/clients/{id}/submissions` → Client's submissions with embedded quotes
   - `GET /api/broker/carriers` → 3 carrier profiles (AIG, Zurich, Travelers)
   - Plus POST/PUT endpoints for CRUD operations

3. **Seed Data Already Present:** `scripts/seed_broker_data.py` had been run previously. Data confirmed in `data/broker/`:
   - 2 clients (Ridgeview: c1111111..., Meridian: c2222222...)
   - 1 submission with 3 embedded quotes (AIG, Zurich, Travelers)
   - 3 carrier profiles

4. **No Code Changes Needed:** All endpoints properly registered and returning correct broker-specific data.

**Key Finding — Local Server Startup:**
- Server requires `STORAGE_BACKEND=local` and `DATABASE_BACKEND=json` env vars for local dev (no Azure/PostgreSQL)
- Without these, startup fails trying to connect to Azure Blob Storage and/or PostgreSQL

**Cross-Agent Coordination (2026-03-25):**
- Coordinated with Frank on frontend persona routing fix
- Frank confirmed early return in `page.tsx` prevents commercial_brokerage from loading underwriting data
- Frontend now correctly routes to BrokerWorkbench with direct dashboard access
- API integration testing ready; no backend changes needed

### 2026-03-25: Created Broker Demo Seed Script with Real Engines

**Task:** Create `scripts/seed_broker_demo.py` that seeds broker demo data using the actual PlacementEngine to score quotes with realistic data.

**Key Files:**
- `scripts/seed_broker_demo.py` — Iterative seed script that creates clients, submissions, quotes, and runs engines
- `app/broker/placement_engine.py` — PlacementEngine used to score quotes
- `data/broker/` — Generated JSON files with scored data

**Implementation:**

**Script Flow:**
1. **Create Clients:** Ridgeview Properties LLC and Meridian Manufacturing Inc
2. **Create Submission:** For Ridgeview with property line of business, quoted status
3. **Create Quotes:** 3 realistic quotes based on sample data files:
   - AIG: $42,500, $18.5M TIV, no exclusions, A+ rating
   - Zurich: $38,750, $18M TIV, 2 exclusions (Mold, Cyber), A+ rating
   - Travelers: $47,200, $19.5M TIV, no exclusions, A++ rating
4. **Create Carrier Profiles:** Financial data for all 3 carriers (FSR, combined ratio, etc.)
5. **Run PlacementEngine:** Score all quotes using composite scoring methodology
6. **Save Scored Quotes:** Embed scored quotes in submission JSON

**PlacementEngine Integration:**
- Engine requires: `List[Quote]`, `Submission`, `Dict[str, CarrierProfile]`
- Scoring factors: Premium (35%), Coverage (30%), Financial Strength (20%), Completeness (15%)
- Engine returns scored quotes sorted by `placement_score` descending
- Top quote gets recommendation rationale explaining the placement decision
- Each quote receives: `placement_score`, `placement_rank`, `coverage_adequacy`, `coverage_gaps`, `premium_percentile`

**Scoring Results (Demo Run):**
- **Zurich ranked #1** (98.0/100): Lowest premium ($38,750), adequate coverage, below-market pricing
- **AIG ranked #2** (87.97/100): Mid-range premium ($42,500), adequate coverage, market pricing
- **Travelers ranked #3** (68.5/100): Highest premium ($47,200), despite A++ rating and best coverage
- Engine recommendation: "Recommended: Zurich. Key factors: Most competitive premium at $38,750; Comprehensive coverage with minimal exclusions; Strong carrier financial rating (A+)."

**Patterns & Conventions:**
- Script designed for iterative execution: Run → Fix bugs → Rerun until clean data
- Uses real engine scoring (not pre-calculated mock data)
- Environment variables required: `STORAGE_BACKEND=local`, `DATABASE_BACKEND=json`
- Quotes embedded in submission JSON (not separate files)
- Clear console output with section headers, checkmarks, and verification steps
- Script prints scoring results and recommendation for manual review

**Key Learning:**
- PlacementEngine heavily weighs premium competitiveness (35% of score)
- Zurich's lowest premium outweighs its exclusions and lower TIV
- Travelers' A++ rating and best coverage don't overcome 11% higher premium
- Engine correctly identifies coverage gaps (missing sublimits) even when adequacy is "adequate"
- Combined ratio adjustments from carrier profiles factor into financial strength scoring

**Data Quality:**
- All quotes have complete fields from sample data files
- Confidence scores vary realistically (lower for fields with issues)
- Coverage gaps identified correctly (Zurich has no flood/EQ gaps despite low confidence scores)
- Premium percentiles computed correctly: Zurich=below_market, AIG/Travelers=market

### 2026-03-25: Systematic Broker API Audit & Fix

**Task:** Audit all 13 broker API endpoints, fix bugs, and produce verified API contract document for Frank's frontend work.

**Bugs Found & Fixed:**

1. **CRITICAL — Compare endpoint 500 error:** `Quote(**dict)` and `Submission(**dict)` don't recursively convert nested dicts (`fields`, `scoring`) to their dataclass types. Caused `'dict' object has no attribute 'annual_premium'` when accessing `q.fields.annual_premium`.
   - **Fix:** Added `_quote_from_dict()` and `_submission_from_dict()` helpers in `app/broker/api.py` that properly reconstruct `QuoteFields`, `PlacementScoring`, and nested types from storage dicts.
   - Also handles LLM returning `deductible` as dict instead of string (normalizes to comma-separated string).
   - Filters to `__dataclass_fields__` keys to prevent `TypeError` from extra storage keys.

2. **Update Client — property_locations dict crash:** `Client(**existing)` would fail if `property_locations` contains plain dicts from storage. Fixed with dict-to-PropertyLocation conversion.

3. **Research endpoint — same Client conversion issue:** Fixed `Client(**client_data)` in research endpoint fallback path.

**Key Files Modified:**
- `app/broker/api.py` — Added `_quote_from_dict()`, `_submission_from_dict()` helpers; fixed `compare_quotes`, `update_client`, `update_submission`, `research_client` endpoints

**All 13 Endpoints Verified:**
1. `GET /api/broker/dashboard` → 200 ✓
2. `GET /api/broker/clients` → 200, array ✓
3. `POST /api/broker/clients` → 201, full client ✓
4. `GET /api/broker/clients/{id}` → 200, client dict ✓
5. `PUT /api/broker/clients/{id}` → 200, updated client ✓
6. `GET /api/broker/clients/{id}/submissions` → 200, array ✓
7. `POST /api/broker/submissions` → 201, full submission ✓
8. `GET /api/broker/submissions/{id}` → 200, with embedded quotes ✓
9. `POST /api/broker/submissions/{id}/quotes` → 201, multipart upload ✓
10. `GET /api/broker/submissions/{id}/quotes` → 200, array ✓
11. `POST /api/broker/submissions/{id}/compare` → 200, comparison+recommendation ✓
12. `POST /api/broker/clients/{id}/research` → 200, brief+sources ✓
13. `GET /api/broker/carriers` → 200, array ✓

**Architecture Pattern — Dict↔Dataclass Conversion:**
- Storage layer returns plain dicts (from JSON files)
- Engine layer expects dataclass instances (Quote, Submission, CarrierProfile)
- API layer must bridge this gap with proper conversion helpers
- Key lesson: Python `dataclasses.asdict()` serializes well, but the reverse (`SomeDataclass(**dict)`) does NOT handle nested dataclass fields — they remain as dicts
- The `_quote_from_dict()` / `_submission_from_dict()` pattern should be used everywhere dicts from storage are converted to dataclass instances

**Output:**
- API contract document written to session files for Frank's frontend integration

## 2026-03-25: Systematic Broker API Audit — All 13 Endpoints Verified & Fixed

**Task:** Complete systematic audit of all 13 broker API endpoints. Test each endpoint. Fix bugs. Write API contract document for Frank's frontend work.

**Work Completed:**
- Tested all 13 endpoints systematically with realistic payloads
- Fixed critical bug in `compare` endpoint: dict-to-dataclass conversion for nested Quote/Submission types
- Fixed `update_client` endpoint: property_locations type conversion 
- Fixed TypeError from extra storage keys not in dataclass fields
- Generated verified API contract document (218 lines) for frontend integration

**Technical Details:**
- **Bug Root Cause:** Python `Quote(**dict)` does NOT recursively convert nested dicts (`fields`, `scoring`, `property_locations`) to dataclass types
- **Solution:** Added `_quote_from_dict()` and `_submission_from_dict()` helpers that:
  1. Recursively reconstruct nested dataclass types (QuoteFields, PlacementScoring, PropertyLocation, CarrierProfile)
  2. Normalize LLM-returned types (e.g., deductible dict → comma-separated string)
  3. Filter keys using `__dataclass_fields__` to prevent TypeError on extra keys
- **Files Modified:** `app/broker/api.py` (218 lines added)

**All 13 Endpoints Verified:**
1. GET /api/broker/dashboard → 200 ✓
2. GET /api/broker/clients → 200 ✓
3. POST /api/broker/clients → 201 ✓
4. GET /api/broker/clients/{id} → 200 ✓
5. PUT /api/broker/clients/{id} → 200 ✓
6. GET /api/broker/clients/{id}/submissions → 200 ✓
7. POST /api/broker/submissions → 201 ✓
8. GET /api/broker/submissions/{id} → 200 ✓
9. POST /api/broker/submissions/{id}/quotes → 201 ✓
10. GET /api/broker/submissions/{id}/quotes → 200 ✓
11. POST /api/broker/submissions/{id}/compare → 200 ✓ (CRITICAL FIX)
12. POST /api/broker/clients/{id}/research → 200 ✓
13. GET /api/broker/carriers → 200 ✓

**Key Pattern for Future Work:**
- All dict-to-dataclass conversions in broker API layer must use the `_quote_from_dict()` / `_submission_from_dict()` helpers
- These helpers are the single source of truth for safe storage→engine data conversion
- Pattern ensures consistency across all endpoints and prevents similar 500 errors in future endpoints
