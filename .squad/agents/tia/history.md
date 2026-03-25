# Tia — History

## Project Context

underwriting-assistant uses pytest for backend testing. Test files follow `test_mortgage_phase*.py` naming. Frontend validation via `npx next build`. Key test areas: mortgage processing phases, API endpoints, document extraction, scoring logic.

## Learnings

### Commercial Brokerage MVP Validation (2025-03-25)

**Module Structure**: The `app.broker` module is organized as a package with dedicated sub-modules: `models.py` (dataclasses), `constants.py` (enums), `storage.py` (JSON persistence), `quote_extractor.py`, `placement_engine.py`, `research_engine.py`, `submission_generator.py`.

**Storage Implementation**: `BrokerStorage` uses JSON files under `data/broker/` with directories for clients, submissions, placements, carriers. Quotes are stored inline within their parent submission. All retrieval methods return dicts (not dataclass instances). Key method signatures: `get_quote(submission_id, quote_id)`, `list_quotes_for_submission(submission_id)`, `get_dashboard_metrics()` returns dict with keys `total_accounts`, `open_submissions`, `total_bound_premium`, `renewals_due_90_days`, `stale_submissions`.

**Placement Engine**: `PlacementEngine.score_quotes()` requires 3 args: `quotes: List[Quote]`, `submission: Submission`, `carrier_profiles: Dict[str, CarrierProfile]`. Scores quotes 0-100 using 4 factors: premium competitiveness (35%), coverage completeness (30%), carrier financial strength (20%), quote completeness (15%). Returns sorted list with `placement_score` and `placement_rank` set on each quote's `scoring` field. `generate_recommendation()` produces human-readable placement rationale.

**Data Model Fields**: `Client` uses `industry_code`, `business_type`, `contacts` (list of dicts), not separate contact fields. `Submission` uses `total_insured_value` (string), `line_of_business` (enum value), status values: `draft`, `submitted`, `quoted`, `bound`, `declined`, `lapsed`. `QuoteFields` has string fields like `annual_premium`, `total_insured_value`, `building_limit`, etc. (not numeric).

**API Integration**: Broker router successfully mounts in `api_server.py` with 97 total routes. Logs confirm "Broker API router registered" on import. Routes include `/api/broker/dashboard`, `/api/broker/clients`, `/api/broker/clients/{client_id}`.

**Testing Dependencies**: Project uses `uv` for package management (not pip directly in venv). Tests requiring `TestClient` need `httpx` installed via `uv pip install httpx`. One pre-existing async test failure requires `pytest-asyncio` plugin (unrelated to new code).

**Persona Config**: Commercial brokerage persona has 37 field schema fields, 5 prompt sections (system, client_research, quote_extraction, placement_recommendation, acord_extraction), enabled=True.

**Frontend Build**: Next.js 14.2.15 build completes successfully with 9 static/dynamic pages, no TypeScript errors, successful linting.

## Validation Completion (2025-03-25)

**Commercial Brokerage MVP: ALL 6 VALIDATION AREAS PASSED**

- ✅ Imports: Clean, no circular dependencies, package structure sound
- ✅ Storage CRUD: JSON persistence functional (create, read, update, delete)
- ✅ Placement Engine: Quote scoring 0-100, ranking correct, recommendations working
- ✅ API Server: 97 routes mounted, key broker endpoints functional
- ✅ Frontend Build: Next.js build succeeded, 9 pages, no errors
- ✅ Tests: 124/135 passing, 10 skipped, 1 pre-existing async failure unrelated to new code

**Status**: MVP ready for integration and deployment.

### 2026-03-25: Backend Engine Wiring Complete

**Update:** Ben completed wiring of all 4 engines into API endpoints. Engine integration endpoints now live:
- Quote upload with extraction (QuoteExtractor)
- Quote comparison with scoring (PlacementEngine)
- Client research with AI insights (ClientResearchEngine)

**Testing Impact:** E2E test coverage needed for all 3 new endpoints. Test cases should include:
- Successful engine execution (happy path)
- Engine failure with graceful fallback (error path)
- Status transitions (RAW → EXTRACTED for quotes)
- Response shape validation against API contracts

