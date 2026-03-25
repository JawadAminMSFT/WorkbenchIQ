# Squad Decisions

## Active Decisions

### Broker UX Redesign — Two-Level Navigation

**Author:** Leo (Lead)  
**Date:** 2026-07-14  
**Status:** Proposed  
**Requested by:** Jawad

#### Context

The Commercial Brokerage UI uses a flat tab architecture in `BrokerWorkbench.tsx` where Dashboard, Research, Submission, and Quotes are all top-level tabs. This doesn't match the spec's workflow (Dashboard → click client → Client Workspace with scoped tabs). Research/Submission/Quotes tabs are disabled by default, there's no client context header, and no back navigation.

#### Decision

Restructure to a two-level view pattern that mirrors how the mortgage workbench works:

1. **BrokerWorkbench** becomes a view switcher: `dashboard` (default) vs `client` (when a client is selected).
2. **ClientWorkspace** (new) is a tabbed workspace scoped to one `clientId` with tabs: Research, Submissions, Quote Comparison.
3. **ClientHeader** (new) provides persistent client context and a back-to-dashboard button.
4. Delete `ClientResearchPanel.tsx`, replace with `ResearchTab.tsx`.
5. Rename `SubmissionBuilder.tsx` → `SubmissionDetail.tsx`.

#### Impact

- **Frank:** ~4 hours of frontend work — 6 new/reworked components, 1 deletion.
- **Ben:** ~2 hours — 2 new API endpoints (client doc upload, package generation), 1 verification.
- **No breaking changes** to existing API contracts. All existing endpoints remain the same.
- **page.tsx** integration unchanged — broker persona still renders BrokerWorkbench directly.

#### Full Blueprint

See `.squad/orchestration-log/2026-07-14T-leo-broker-redesign.md` for complete implementation details including component props, API contracts, state management, and implementation order.

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
