# Work Routing

How to decide who handles what.

## Routing Table

| Work Type | Route To | Examples |
|-----------|----------|----------|
| Architecture & design | Leo | System design, tech decisions, cross-cutting concerns |
| Frontend UI | Frank | React/Next.js components, styling, UI bugs, frontend tests |
| Backend & APIs | Ben | Python endpoints, scoring engine, data processing, API changes |
| Testing & QA | Tia | pytest, E2E tests, regression hunting, test coverage |
| Mobile & responsive | Marty | React Native, responsive design, cross-platform features |
| DevOps & infra | Denise | CI/CD, Azure deploy, GitHub Actions, environment config |
| Product & priorities | Nina | User stories, requirements, backlog, acceptance criteria |
| AI & ML | Ada | LLM prompts, Azure OpenAI, document extraction, model tuning |
| Domain & compliance | Rex | Underwriting rules, regulatory, industry standards, scoring accuracy |
| Code review | Leo | Review PRs, check quality, suggest improvements |
| Testing strategy | Leo + Tia | Define what to test, coverage gaps, test plans |
| Scope & priorities | Nina + Leo | What to build next, trade-offs, decisions |
| Session logging | Scribe | Automatic — never needs routing |
| Work monitoring | Wearsy | Issue triage, PR tracking, CI health, board status |

## Issue Routing

| Label | Action | Who |
|-------|--------|-----|
| `squad` | Triage: analyze issue, assign `squad:{member}` label | Leo |
| `squad:leo` | Architecture, design, code review | Leo |
| `squad:frank` | Frontend UI work | Frank |
| `squad:ben` | Backend, API, scoring | Ben |
| `squad:tia` | Testing, QA | Tia |
| `squad:marty` | Mobile, responsive | Marty |
| `squad:denise` | DevOps, CI/CD, deploy | Denise |
| `squad:nina` | Product requirements, priorities | Nina |
| `squad:ada` | AI/ML, prompts, extraction | Ada |
| `squad:rex` | Domain expertise, compliance | Rex |

### How Issue Assignment Works

1. When a GitHub issue gets the `squad` label, **Leo** triages it — analyzing content, assigning the right `squad:{member}` label, and commenting with triage notes.
2. When a `squad:{member}` label is applied, that member picks up the issue in their next session.
3. Members can reassign by removing their label and adding another member's label.
4. The `squad` label is the "inbox" — untriaged issues waiting for Leo's review.

## Rules

1. **Eager by default** — spawn all agents who could usefully start work, including anticipatory downstream work.
2. **Scribe always runs** after substantial work, always as `mode: "background"`. Never blocks.
3. **Quick facts → coordinator answers directly.** Don't spawn an agent for "what port does the server run on?"
4. **When two agents could handle it**, pick the one whose domain is the primary concern.
5. **"Team, ..." → fan-out.** Spawn all relevant agents in parallel as `mode: "background"`.
6. **Anticipate downstream work.** If a feature is being built, spawn Tia to write test cases from requirements simultaneously.
7. **Issue-labeled work** — when a `squad:{member}` label is applied to an issue, route to that member. Leo handles all `squad` (base label) triage.
8. **AI work → Ada first.** Anything involving prompts, LLM integration, or document extraction goes to Ada.
9. **Domain questions → Rex.** Regulatory, underwriting rules, or industry standards route to Rex.
10. **Product scope → Nina.** Requirements, priorities, and user stories go to Nina.
