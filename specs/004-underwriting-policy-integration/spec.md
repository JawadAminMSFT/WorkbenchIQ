# Spec 004: Underwriting Policy Integration with Chat Experience

## Overview

This specification defines the implementation of a comprehensive underwriting policy system for WorkbenchIQ, including:

1. **Underwriting Policy File** - A JSON-based underwriting manual for life & health applications
2. **Policy-Driven Risk Ratings** - Risk assessments with rationale and policy citations
3. **Risk Rating Popovers** - Hover-based UI showing rationale and policy references
4. **Policy Report Modal** - Full policy evaluation summary with PDF export
5. **Recommended Action Panel** - Summary version of policy report in PatientSummary
6. **Underwriter Chat** - Context-aware chat with policy and application injection
7. **Chat History** - Persistent chat sessions per application with slide-out drawer

---

## User Stories

### US-1: Underwriting Policy Reference
> As an underwriter, I want the system to use a documented underwriting policy manual when generating risk ratings, so that decisions are consistent and auditable.

### US-2: Risk Rating Transparency
> As an underwriter, I want to hover over any risk rating and see the rationale and policy citation, so I understand how the decision was made.

### US-3: Policy Report
> As an underwriter, I want to run a full policy check against an application and see a summary report, so I can review all risk factors at once.

### US-4: PDF Export
> As an underwriter, I want to export the policy report as a PDF, so I can share it with colleagues or attach it to the case file.

### US-5: Recommended Action Consistency
> As an underwriter, I want the "Recommended Action" panel to show a summary of the policy report, so the UI is consistent.

### US-6: Underwriter Chat
> As an underwriter, I want to ask questions about an application in a chat interface, where the AI has full context of both the application and underwriting policies.

### US-7: Chat History
> As an underwriter, I want to see my past chat conversations for each application and switch between them, while keeping the current chat focused on the selected application.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ RiskRating      │  │ PolicyReport    │  │ Ask IQ (ChatDrawer)         │  │
│  │ Popover         │  │ Modal           │  │ ┌─────────────────────────┐ │  │
│  │ - Rationale     │  │ - Summary       │  │ │ Floating Button (FAB)   │ │  │
│  │ - Policy cite   │  │ - All ratings   │  │ │ Bottom-right of screen  │ │  │
│  │ - Hover trigger │  │ - PDF export    │  │ │ Opens slide-out drawer  │ │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PolicySummaryPanel (replaces simple Recommended Action)              │    │
│  │ - Overall risk level                                                 │    │
│  │ - Key policy evaluations (condensed)                                 │    │
│  │ - "View Full Report" button                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                                                                              │
│  New Endpoints:                                                              │
│  ├── GET  /api/underwriting-policies                                        │
│  ├── POST /api/applications/{id}/run-policy-check                           │
│  ├── POST /api/applications/{id}/chat                                       │
│  ├── GET  /api/applications/{id}/chats                                      │
│  ├── GET  /api/applications/{id}/chats/{chat_id}                            │
│  └── DELETE /api/applications/{id}/chats/{chat_id}                          │
│                                                                              │
│  New Modules:                                                                │
│  ├── app/underwriting_policies.py  (Policy loader & injector)               │
│  └── app/chat_service.py           (Chat with context injection)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  data/life-health-underwriting-policies.json                                 │
│  data/applications/{id}/chats/{chat_id}.json                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### 1. Underwriting Policy Schema (`life-health-underwriting-policies.json`)

```json
{
  "version": "1.0",
  "effective_date": "2025-01-01",
  "description": "Life and Health Insurance Underwriting Manual",
  "policies": [
    {
      "id": "CVD-BP-001",
      "category": "cardiovascular",
      "subcategory": "hypertension",
      "name": "Blood Pressure Risk Assessment",
      "description": "Guidelines for evaluating blood pressure readings",
      "criteria": [
        {
          "id": "CVD-BP-001-A",
          "condition": "Systolic < 120 AND Diastolic < 80",
          "risk_level": "Low",
          "action": "Standard rates",
          "rationale": "Normal blood pressure per AHA guidelines"
        },
        {
          "id": "CVD-BP-001-B",
          "condition": "Systolic 120-139 OR Diastolic 80-89",
          "risk_level": "Low-Moderate",
          "action": "Standard rates if controlled on single medication",
          "rationale": "Elevated/Stage 1 hypertension, acceptable if well-controlled"
        },
        {
          "id": "CVD-BP-001-C",
          "condition": "Systolic 140-159 OR Diastolic 90-99",
          "risk_level": "Moderate",
          "action": "Consider +25-50% loading",
          "rationale": "Stage 2 hypertension requires premium adjustment"
        },
        {
          "id": "CVD-BP-001-D",
          "condition": "Systolic >= 160 OR Diastolic >= 100",
          "risk_level": "High",
          "action": "Defer pending control, or +75-100% loading",
          "rationale": "Severe hypertension with significant mortality risk"
        }
      ],
      "modifying_factors": [
        "Duration of condition",
        "Medication compliance",
        "End-organ damage (LVH, retinopathy, nephropathy)",
        "Comorbidities (diabetes, kidney disease, obesity)"
      ],
      "references": [
        "AHA/ACC Hypertension Guidelines 2024",
        "SOA Mortality Studies 2023"
      ]
    }
  ]
}
```

### 2. Enhanced LLM Output with Policy Citations

```json
{
  "summary": "...",
  "risk_assessment": "Low-Moderate",
  "risk_rationale": "Applicant shows well-controlled hypertension on single-agent therapy with readings averaging 126/81 mmHg. No evidence of end-organ damage. Non-smoker status and regular exercise are favorable factors.",
  "policy_citations": [
    {
      "policy_id": "CVD-BP-001",
      "criteria_id": "CVD-BP-001-B",
      "policy_name": "Blood Pressure Risk Assessment",
      "matched_condition": "Systolic 120-139 OR Diastolic 80-89",
      "applied_action": "Standard rates if controlled on single medication",
      "rationale": "Elevated/Stage 1 hypertension, acceptable if well-controlled"
    }
  ],
  "underwriting_action": "Recommend approval at standard rates."
}
```

### 3. Chat Session Schema

```json
{
  "id": "chat-uuid-123",
  "application_id": "a1b2c3d4",
  "created_at": "2025-12-15T10:30:00Z",
  "updated_at": "2025-12-15T10:45:00Z",
  "title": "Questions about hypertension rating",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Why was this applicant rated as Low-Moderate?",
      "timestamp": "2025-12-15T10:30:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "Based on policy CVD-BP-001 (Blood Pressure Risk Assessment)...",
      "timestamp": "2025-12-15T10:30:05Z"
    }
  ]
}
```

### 4. Policy Report Schema

```json
{
  "application_id": "a1b2c3d4",
  "generated_at": "2025-12-15T10:45:00Z",
  "applicant_name": "Sarah Chen",
  "external_reference": "UW-2025-5432",
  "overall_risk_level": "Low-Moderate",
  "recommended_action": "Approve at standard rates",
  "evaluations": [
    {
      "category": "cardiovascular",
      "policy_id": "CVD-BP-001",
      "policy_name": "Blood Pressure Risk Assessment",
      "risk_level": "Low-Moderate",
      "summary": "Well-controlled hypertension on single-agent therapy",
      "criteria_matched": "CVD-BP-001-B",
      "action": "Standard rates if controlled on single medication"
    },
    {
      "category": "metabolic",
      "policy_id": "META-CHOL-001",
      "policy_name": "Cholesterol Risk Assessment",
      "risk_level": "Low",
      "summary": "Borderline LDL, excellent HDL ratio",
      "criteria_matched": "META-CHOL-001-A",
      "action": "Standard rates"
    }
  ],
  "modifying_factors_applied": [
    "Non-smoker: -10% mortality adjustment",
    "Regular exercise: favorable consideration"
  ],
  "pending_requirements": []
}
```

---

## Feature Breakdown

### Feature 4.1: Underwriting Policy File
Create `data/life-health-underwriting-policies.json` with comprehensive policy definitions.

### Feature 4.2: Policy Loader Module
Backend module to load, validate, and provide policies.

### Feature 4.3: Policy Injection into Prompts
Modify prompts to include policy context and require structured citations.

### Feature 4.4: Risk Rating Popover
Frontend component showing rationale and policy on hover.

### Feature 4.5: Policy Report Modal
Full policy evaluation with PDF export capability.

### Feature 4.6: Policy Summary Panel
Replace "Recommended Action" with a policy-aligned summary panel.

### Feature 4.7: Chat Service Backend
Chat API with context injection for policies and application data.

### Feature 4.8: Chat Slide-out Drawer
Frontend chat UI with history sidebar and message window.

---

## Files to Create/Modify

### New Files
| File | Description |
|------|-------------|
| `data/life-health-underwriting-policies.json` | Underwriting policy manual |
| `app/underwriting_policies.py` | Policy loader and injector |
| `app/chat_service.py` | Chat service with context injection |
| `frontend/src/components/RiskRatingPopover.tsx` | Hover popover for risk ratings |
| `frontend/src/components/PolicyReportModal.tsx` | Full policy report modal |
| `frontend/src/components/PolicySummaryPanel.tsx` | Summary panel for PatientSummary |
| `frontend/src/components/chat/ChatDrawer.tsx` | Slide-out chat drawer container |
| `frontend/src/components/chat/ChatWindow.tsx` | Chat message display and input |
| `frontend/src/components/chat/ChatList.tsx` | Chat history sidebar |
| `frontend/src/components/chat/ChatMessage.tsx` | Individual message bubble |
| `frontend/src/lib/ChatContext.tsx` | React context for chat state |

### Modified Files
| File | Changes |
|------|---------|
| `api_server.py` | Add new API endpoints |
| `app/processing.py` | Inject policies into prompts |
| `app/personas.py` | Update prompt templates for citations |
| `data/prompts.json` | Update prompts to require policy citations |
| `frontend/src/lib/types.ts` | Add new TypeScript types |
| `frontend/src/lib/api.ts` | Add API client methods |
| `frontend/src/components/PatientSummary.tsx` | Integrate PolicySummaryPanel |
| `frontend/src/components/LabResultsPanel.tsx` | Use RiskRatingPopover |
| `frontend/src/components/FamilyHistoryPanel.tsx` | Use RiskRatingPopover |
| `frontend/src/app/page.tsx` | Add PolicyReportModal and ChatDrawer |

---

## API Endpoints

### GET /api/underwriting-policies
Returns the full underwriting policy manual.

**Response:**
```json
{
  "version": "1.0",
  "effective_date": "2025-01-01",
  "policies": [...]
}
```

### POST /api/applications/{id}/run-policy-check
Re-runs all policy evaluations against the application.

**Response:**
```json
{
  "application_id": "a1b2c3d4",
  "generated_at": "...",
  "overall_risk_level": "Low-Moderate",
  "evaluations": [...],
  "recommended_action": "..."
}
```

### POST /api/applications/{id}/chat
Sends a message and receives AI response with full context.

**Request:**
```json
{
  "chat_id": "optional-existing-chat-id",
  "message": "Why was this applicant rated Low-Moderate?"
}
```

**Response:**
```json
{
  "chat_id": "chat-uuid",
  "message_id": "msg-uuid",
  "response": "Based on policy CVD-BP-001...",
  "timestamp": "2025-12-15T10:30:05Z"
}
```

### GET /api/applications/{id}/chats
Lists all chat sessions for an application.

**Response:**
```json
{
  "chats": [
    {
      "id": "chat-uuid",
      "title": "Questions about hypertension",
      "created_at": "...",
      "updated_at": "...",
      "message_count": 4
    }
  ]
}
```

### GET /api/applications/{id}/chats/{chat_id}
Gets full chat session with all messages.

### DELETE /api/applications/{id}/chats/{chat_id}
Deletes a chat session.

---

## UI Components

### RiskRatingPopover
- Triggered on hover over any risk badge
- Shows: risk level, rationale, policy citation
- Styled with Tailwind (white bg, shadow, rounded)

### PolicyReportModal
- Full-screen Tailwind modal
- Header: Application info, generated timestamp
- Body: Overall assessment + list of policy evaluations
- Footer: "Re-run Policy Check" + "Export PDF" buttons
- PDF export via browser print or jsPDF

### PolicySummaryPanel
- Replaces simple "Recommended Action" in PatientSummary
- Shows: Overall risk badge, 3-4 key policy evaluations (condensed)
- "View Full Report" button opens PolicyReportModal

### ChatDrawer ("Ask IQ")
- Floating action button (FAB) at bottom-right of screen when closed
- FAB displays "Ask IQ" label with chat icon
- Message count badge shown on FAB when there are messages
- Clicking FAB opens slide-out drawer from right side
- Drawer shows chat interface with message history
- Auto-loads past chat history from localStorage per application

### ChatWindow
- Scrollable message area
- User messages right-aligned (blue)
- Assistant messages left-aligned (gray)
- Input area at bottom with send button
- Loading indicator while waiting for response

### ChatList
- List of past chats for current application only
- Shows title, date, message count
- Active chat highlighted
- "New Chat" button at top
- Delete option on each chat

---

## Implementation Notes

### Token Limit Handling
- Policies are large; inject only relevant sections based on extracted conditions
- For chat, use summarized application context + full policies
- Consider chunking if context exceeds limits

### PDF Export Strategy
- Use browser's `window.print()` with print-specific CSS
- Alternatively, use `jspdf` + `html2canvas` for client-side generation
- Modal has a "print-friendly" variant for export

### Chat Context Injection
System prompt for chat will include:
1. Full underwriting policy manual (or relevant sections)
2. Application summary and key extracted fields
3. Previous LLM analysis outputs
4. Instructions to cite policies when answering

### Backward Compatibility
- Existing applications without policy citations show "No policy citation available"
- Policy report can still be generated by re-running analysis

---

## Success Criteria

1. ✅ `life-health-underwriting-policies.json` exists with 10+ policy definitions
2. ✅ Risk ratings in UI show popover with rationale and policy citation
3. ✅ Policy report modal shows all evaluations with PDF export
4. ✅ PatientSummary shows policy-aligned summary panel
5. ✅ Chat drawer allows Q&A with policy+application context
6. ✅ Chat history persists and can be reviewed/deleted
7. ✅ Switching applications resets chat to new session

---

## Out of Scope (Future)

- Admin UI for editing policies (file-only for now)
- Chat session sharing between users
- Policy version history/diff
- Automated policy compliance scoring
