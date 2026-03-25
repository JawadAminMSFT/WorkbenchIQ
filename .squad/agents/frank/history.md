# Frank — History

## Project Context

underwriting-assistant frontend is a Next.js application with TypeScript and React. Uses Tailwind CSS for styling. Key UI includes document upload, policy checks panels, scoring displays, and underwriting workflow views.

## Learnings

### Session: Commercial Brokerage Workbench Build

**Files created/modified:**
- `frontend/src/lib/broker-types.ts` — All TypeScript interfaces for the broker domain (Client, Submission, Quote, ComparisonResult, ResearchBrief, etc.)
- `frontend/src/lib/broker-api.ts` — Typed fetch functions mirroring `api.ts` patterns (relative URLs, BrokerAPIError, FormData for uploads)
- `frontend/src/components/broker/BrokerWorkbench.tsx` — Main container with 4 tabs (Dashboard, Submission, Quotes, Research), amber accent color
- `frontend/src/components/broker/BrokerDashboard.tsx` — Metrics cards + accounts list, fetches dashboard + clients
- `frontend/src/components/broker/QuoteComparisonTable.tsx` — Side-by-side carrier comparison table with color-coded cells, AI recommendation, placement scores
- `frontend/src/components/broker/SubmissionBuilder.tsx` — ACORD field display, document list, drag-and-drop quote upload
- `frontend/src/components/broker/ClientResearchPanel.tsx` — AI research brief viewer with confidence bars and citation links
- `frontend/src/components/broker/index.ts` — Updated to re-export all 5 components

**Architecture decisions:**
- Kept broker-api.ts separate from main api.ts to avoid bloating the shared module. Own `BrokerAPIError` class and `apiFetch` wrapper.
- Amber (#d97706 / amber-600) is the broker persona accent color (vs emerald for mortgage).
- Tab state in BrokerWorkbench drives which sub-component is shown; selectedSubmissionId and selectedClientId propagate to child components.
- All components follow the same loading → error → empty → data state pattern from MortgageWorkbench.
- Quote upload uses FormData (not JSON) since it sends binary files.
- ACORD fields grouped by form type (125/140) with confidence badges and "Needs Review" indicators.

**Patterns confirmed:**
- `'use client'` directive mandatory on all interactive components.
- lucide-react for all icons.
- Tailwind-only styling, no CSS modules.
- Export pattern: `export { default as X } from './X';` in index.ts.

### 2026-03-25: Backend Engine Integration Complete

**Status Update:** Ben completed wiring of 4 backend engines into API router. Three new endpoints now available for frontend integration:
- `POST /api/broker/submissions/{submission_id}/quotes` — QuoteExtractor (extracts & saves quote fields)
- `POST /api/broker/submissions/{submission_id}/compare` — PlacementEngine (returns scored quotes + AI recommendation)
- `POST /api/broker/clients/{client_id}/research` — ClientResearchEngine (returns research brief markdown)

**For Frontend:** Response shapes finalized. Components can now call real endpoints instead of mock data. BrokerWorkbench, QuoteComparisonTable, and ClientResearchPanel should consume these endpoints (see orchestration log for exact contract).

