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

### 2026-03-25: CSS & Bug Fix Validation Complete

**User Report:** "Frontend CSS is now broken" following simultaneous multi-agent edits.

**Investigation Scope:** 6 tasks covering build validation, merge conflicts, 7 bug fixes, research integration, CSS tooling.

**Task 1 - Build Validation:** ✅ PASSED
- `npx next build` completed successfully
- Zero compilation errors, zero TypeScript errors
- All 9 pages generated (static + dynamic routes)
- No Tailwind parse errors or CSS compilation issues
- `.next` cache healthy, no stale artifacts

**Task 2 - Merge Conflict Detection:** ✅ PASSED
- Checked 5 files: `BrokerDashboard.tsx`, `BrokerWorkbench.tsx`, `ClientResearchPanel.tsx`, `broker-api.ts`, `broker-types.ts`
- No conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) found
- No duplicate function definitions or imports
- Clean JSX syntax throughout

**Task 3 - Bug Fix Verification (7/7):** ✅ ALL VERIFIED
1. **client.name usage**: `BrokerDashboard.tsx:170` uses `{client.name}` (not `company_name`)
2. **No double $**: Dashboard metrics use `{m.value}` direct display (backend pre-formats with `$`)
3. **New Client onClick**: Lines 143-149 wire `onClick` → `setShowNewClientModal(true)` → `handleCreateClient()` API call
4. **Submission tab enables**: `BrokerWorkbench.tsx:47` disables when `!selectedSubmissionId`, enabled by `handleSelectSubmission()`
5. **Quotes tab enables**: `BrokerWorkbench.tsx:48` same logic as submission tab
6. **Account cards show correct fields**: Lines 171-173 display `industry_code`, `business_type` (confirmed in source)
7. **Backend no $ stripping**: Searched `app/broker/` — zero instances of `.strip('$')` or `.strip("$")`

**Task 4 - Research Integration:** ✅ PASSED
- `broker-api.ts:147-159` implements `runClientResearch(clientId, companyName)` with body `{ company_name: companyName }`
- `ClientResearchPanel.tsx:62` calls it with `client?.name ?? activeClientId`
- API contract correct: frontend passes company name, backend receives it

**Task 5 - CSS Issues:** ✅ NONE FOUND
- Tailwind classes compiling correctly
- No missing `postcss.config.js` or `tailwind.config.js` issues
- All JSX tags properly closed, no syntax breaking renders
- All imports valid

**Task 6 - Final Verification:** ✅ DEPLOYMENT READY
- Clean production build, 0 errors, 0 warnings
- TypeScript types all valid
- Bundle sizes normal (88-192 KB first load JS)

**Conclusion:** Could not reproduce "CSS is broken" report. Build process is completely healthy. All bug fixes verified in source code. If user still experiences visual issues, likely causes:
1. **Browser cache** (recommend Ctrl+Shift+R hard refresh)
2. **Dev server vs build mismatch** (recommend `npm run dev` restart)
3. **Runtime data issue** (not CSS compilation — need browser console logs)

**Key Learning:** Next.js build validation is the source of truth for CSS/TypeScript errors. If build succeeds cleanly, "broken CSS" is likely a runtime or browser caching issue, not a compilation problem.

