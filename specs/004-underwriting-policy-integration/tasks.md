# Spec 004: Implementation Tasks

## Status Legend
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Blocked

---

## Phase 1: Backend - Policy Infrastructure

### Task 1.1: Create Underwriting Policy JSON File
**Status:** ✅ Completed  
**File:** `data/life-health-underwriting-policies.json`  
**Description:** Create comprehensive underwriting policy manual with policies for:
- Blood pressure/hypertension (CVD-BP-001)
- Cholesterol/dyslipidemia (CVD-CHOL-001)
- Family history - cardiovascular (FAM-CVD-001)
- Family history - cancer (FAM-CA-001)
- Tobacco use (LIFE-TOB-001)
- Alcohol use (LIFE-ALC-001)
- BMI/obesity (META-BMI-001)
- Thyroid conditions (ENDO-THY-001)
- Occupation hazards (LIFE-OCC-001)

### Task 1.2: Create Policy Loader Module
**Status:** ✅ Completed  
**File:** `app/underwriting_policies.py`  
**Description:** Python module with:
- `PolicyLoader` class with caching
- `load_policies()` - Load and parse policies
- `get_policy_by_id(policy_id: str)` - Get single policy by ID
- `get_relevant_policies(categories: list)` - Filter by category
- `get_policies_for_prompt()` - Format for LLM injection
- Data classes: `PolicyCriteria`, `UnderwritingPolicy`

### Task 1.3: Modify Prompt Templates for Policy Citations
**Status:** ✅ Completed  
**Files:** `data/prompts.json`  
**Description:** Updated all risk-generating prompts to:
- Include `{underwriting_policies}` placeholder
- Require `policy_citations` array in output with structure:
  - `policy_id`, `policy_name`, `criteria_applied`, `finding`, `rating_impact`
- Updated: customer_profile, family_history, hypertension, high_cholesterol, other_medical_findings, recommended_action

### Task 1.4: Modify Processing to Inject Policies
**Status:** ✅ Completed  
**File:** `app/processing.py`  
**Description:** Updated:
- Import `PolicyLoader` from `underwriting_policies.py`
- Added `load_underwriting_policies()` function
- Modified `_run_single_prompt()` to inject policies via `{underwriting_policies}` placeholder
- Modified `_run_section_prompts()` to pass `underwriting_policies` parameter
- Modified `run_underwriting_prompts()` to load and pass policies to all prompts

### Task 1.5: Add Policy Retrieval API Endpoint
**Status:** ✅ Completed  
**File:** `api_server.py`  
**Description:** Added endpoints:
- `GET /api/policies` - Returns all policies with full details
- `GET /api/policies/{policy_id}` - Get single policy by ID
- `GET /api/policies/category/{category}` - Get policies by category

### Task 1.6: Add Chat API Endpoint
**Status:** ✅ Completed  
**File:** `api_server.py`  
**Description:** Added endpoint:
- `POST /api/applications/{id}/chat` - Chat about application with policy context
- Includes application data, LLM outputs, and underwriting policies in context

### Task 1.7: Configure Chat Model (gpt-4.1-mini)
**Status:** ✅ Completed  
**Files:** `app/config.py`, `app/openai_client.py`, `api_server.py`, `.env.example`  
**Description:** Added separate model configuration for Ask IQ chat:
- Added `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` env var (default: `gpt-4-1-mini`)
- Added `AZURE_OPENAI_CHAT_MODEL_NAME` env var (default: `gpt-4.1-mini`)
- Extended `OpenAISettings` dataclass with `chat_deployment_name` and `chat_model_name` fields
- Updated `load_settings()` to load chat model settings
- Updated `chat_completion()` to accept `deployment_override` and `model_override` params
- Modified chat endpoint to use chat-specific deployment instead of main analysis model

---

## Phase 2: Frontend - Risk Rating Popovers

### Task 2.1: Create RiskRatingPopover Component
**Status:** ✅ Completed  
**File:** `frontend/src/components/RiskRatingPopover.tsx`  
**Description:** Created popover component with:
- Hover/click trigger on risk badges
- Displays rationale and policy citations
- Color-coded by risk level (high/moderate/low)
- Click-through to policy details

### Task 2.2: Update PatientSummary Component
**Status:** ✅ Completed  
**File:** `frontend/src/components/PatientSummary.tsx`  
**Description:** Updated to:
- Use `RiskRatingPopover` instead of plain badge
- Pass policy citations from LLM output
- Support `onPolicyClick` callback

---

## Phase 3: Frontend - Policy Report Modal

### Task 3.1: Create PolicyReportModal Component
**Status:** ✅ Completed  
**File:** `frontend/src/components/PolicyReportModal.tsx`  
**Description:** Created modal with:
- Overall risk assessment header
- List of all policy citations from all sections
- Re-run analysis button
- Export to PDF functionality (via print dialog)
- Escape key and click-outside to close

---

## Phase 4: Frontend - Chat Drawer

### Task 4.1: Create ChatDrawer Component
**Status:** ✅ Completed  
**File:** `frontend/src/components/ChatDrawer.tsx`  
**Description:** Created slide-out drawer with:
- Right-side slide-out animation
- Chat message history display
- User/assistant message styling
- Suggested prompts for empty state
- localStorage persistence per application
- Clear history functionality
- Send on Enter, new line on Shift+Enter

---

## Phase 5: Frontend - Policy Summary Panel

### Task 5.1: Create PolicySummaryPanel Component
**Status:** ✅ Completed  
**File:** `frontend/src/components/PolicySummaryPanel.tsx`  
**Description:** Created panel with:
- Overall risk rating with icon
- Recommendation summary from LLM
- Top 3 policy citations
- Total citation count
- Buttons: View Full Report, Ask Questions

### Task 5.2: Integrate into Main Page
**Status:** ✅ Completed  
**File:** `frontend/src/app/page.tsx`  
**Description:** Updated main page to:
- Import PolicySummaryPanel, PolicyReportModal, ChatDrawer
- Add state for modal/drawer open status
- Add PolicySummaryPanel after PatientSummary
- Wire up modal and drawer triggers
- Add re-run analysis handler

---

## Phase 6: Type Definitions

### Task 6.1: Add Policy Types
**Status:** ✅ Completed  
**File:** `frontend/src/lib/types.ts`  
**Description:** Added types:
- `PolicyCriteria` - condition, rating, notes
- `UnderwritingPolicy` - full policy definition
- `PolicyCitation` - LLM citation output
- `ParsedOutputWithCitations` - extended parsed output
- `PoliciesResponse`, `PolicyResponse` - API responses

---

## Phase 7: Testing & Documentation (Remaining)

### Task 7.1: Backend Unit Tests
**Status:** ⬜ Not Started  
**Files:** `tests/test_underwriting_policies.py`, `tests/test_chat.py`

### Task 7.2: Frontend Component Tests
**Status:** ⬜ Not Started  
**Files:** `frontend/src/components/__tests__/`

### Task 7.3: Integration Tests
**Status:** ⬜ Not Started  
**Description:** E2E tests for policy flow and chat

### Task 7.4: Update README
**Status:** ⬜ Not Started  
**File:** `README.md`

### Task 7.5: Update Quickstart Guide
**Status:** ⬜ Not Started  
**File:** `specs/004-underwriting-policy-integration/quickstart.md`

---

## Phase 3: Frontend - TypeScript Types & API

### Task 3.1: Add TypeScript Types
**Status:** ⬜ Not Started  
**File:** `frontend/src/lib/types.ts`  
**Description:** Add types:
- `UnderwritingPolicy`, `PolicyCriteria`, `PolicyCitation`
- `PolicyReport`, `PolicyEvaluation`
- `ChatSession`, `ChatMessage`, `ChatSummary`
- `EnhancedParsedOutput` (extends ParsedOutput with rationale/citations)

### Task 3.2: Add API Client Methods
**Status:** ⬜ Not Started  
**File:** `frontend/src/lib/api.ts`  
**Description:** Add functions:
- `getUnderwritingPolicies(): Promise<UnderwritingPolicies>`
- `runPolicyCheck(appId: string): Promise<PolicyReport>`
- `sendChatMessage(appId: string, chatId: string | null, message: string): Promise<ChatResponse>`
- `listChats(appId: string): Promise<ChatSummary[]>`
- `getChat(appId: string, chatId: string): Promise<ChatSession>`
- `deleteChat(appId: string, chatId: string): Promise<void>`

---

## Phase 4: Frontend - Risk Rating Popover

### Task 4.1: Create RiskRatingPopover Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/RiskRatingPopover.tsx`  
**Description:** Tailwind popover component:
- Props: `riskLevel`, `rationale`, `policyCitations`, `children` (trigger element)
- Uses Headless UI Popover or custom hover state
- Shows risk level badge, rationale text, policy citations list
- Each citation shows policy name and matched condition
- Styled: white bg, shadow-lg, rounded-lg, max-w-sm

### Task 4.2: Update PatientSummary with Popover
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/PatientSummary.tsx`  
**Description:** 
- Wrap risk badge with RiskRatingPopover
- Extract rationale and citations from `customer_profile.parsed`
- Fallback text if no citations available

### Task 4.3: Update LabResultsPanel with Popover
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/LabResultsPanel.tsx`  
**Description:**
- Wrap "Risk Assessment" section with RiskRatingPopover
- Extract from `hypertension.parsed` or `high_cholesterol.parsed`

### Task 4.4: Update FamilyHistoryPanel with Popover
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/FamilyHistoryPanel.tsx`  
**Description:**
- Wrap risk badge with RiskRatingPopover
- Extract from `family_history.parsed`

---

## Phase 5: Frontend - Policy Report Modal

### Task 5.1: Create PolicyReportModal Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/PolicyReportModal.tsx`  
**Description:** Full Tailwind modal:
- Props: `isOpen`, `onClose`, `application`, `report` (optional, fetches if not provided)
- Header: Application name, reference, generated timestamp
- Overall assessment section with large risk badge
- Evaluations list: category icon, policy name, risk level, summary
- Modifying factors section
- Footer: "Re-run Policy Check" button (with loading state), "Export PDF" button
- PDF export via `window.print()` with `@media print` styles

### Task 5.2: Create PolicySummaryPanel Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/PolicySummaryPanel.tsx`  
**Description:** Compact panel for PatientSummary:
- Shows overall risk level badge (large)
- 3-4 condensed policy evaluations (icon + name + risk)
- Recommended action text
- "View Full Report" button → opens PolicyReportModal
- Replaces the simple "Recommended Action" div

### Task 5.3: Integrate PolicySummaryPanel into PatientSummary
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/PatientSummary.tsx`  
**Description:**
- Replace the `underwritingAction` div with `<PolicySummaryPanel>`
- Pass application and policy citations data

### Task 5.4: Add Policy Report Button to Page Header
**Status:** ⬜ Not Started  
**File:** `frontend/src/app/page.tsx`  
**Description:**
- Add "Run Policy Check" button near application header
- Opens PolicyReportModal
- Shows loading state while running

---

## Phase 6: Frontend - Chat Slide-out Drawer

### Task 6.1: Create ChatMessage Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/chat/ChatMessage.tsx`  
**Description:** Message bubble:
- Props: `role` ('user' | 'assistant'), `content`, `timestamp`
- User: right-aligned, blue bg, white text
- Assistant: left-aligned, gray bg, dark text
- Timestamp below in muted text
- Support markdown rendering in assistant messages

### Task 6.2: Create ChatWindow Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/chat/ChatWindow.tsx`  
**Description:** Main chat area:
- Props: `chatId`, `applicationId`, `messages`, `onSendMessage`
- Scrollable message container (auto-scroll to bottom)
- Input area: textarea + send button
- Loading indicator while waiting for response
- Empty state: "Start a conversation about this application"

### Task 6.3: Create ChatList Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/chat/ChatList.tsx`  
**Description:** Chat history sidebar:
- Props: `chats`, `activeChatId`, `onSelectChat`, `onNewChat`, `onDeleteChat`
- "New Chat" button at top
- List of chat items: title, date, message count
- Active chat highlighted with bg color
- Delete button (trash icon) on hover
- Empty state: "No previous chats"

### Task 6.4: Create ChatDrawer Component
**Status:** ⬜ Not Started  
**File:** `frontend/src/components/chat/ChatDrawer.tsx`  
**Description:** Slide-out drawer container:
- Props: `isOpen`, `onClose`, `applicationId`
- Fixed position, slides in from right
- Width: ~500px (or responsive)
- Header: "Underwriter Assistant" + close button
- Body: ChatList (collapsible) + ChatWindow
- Backdrop overlay when open

### Task 6.5: Create ChatContext Provider
**Status:** ⬜ Not Started  
**File:** `frontend/src/lib/ChatContext.tsx`  
**Description:** React context for chat state:
- `currentChatId`, `setCurrentChatId`
- `chats`, `refreshChats`
- `messages`, `sendMessage`
- `isDrawerOpen`, `openDrawer`, `closeDrawer`
- Auto-refresh chats when application changes
- Auto-create new chat when switching applications

### Task 6.6: Integrate ChatDrawer into Main Page
**Status:** ⬜ Not Started  
**File:** `frontend/src/app/page.tsx`  
**Description:**
- Add ChatContext provider
- Add floating "Chat" button (bottom-right FAB or TopNav button)
- Render ChatDrawer component
- Pass selected application ID

---

## Phase 7: Testing & Polish

### Task 7.1: Backend Unit Tests
**Status:** ⬜ Not Started  
**Files:** `tests/test_underwriting_policies.py`, `tests/test_chat_service.py`  
**Description:**
- Test policy loading and validation
- Test policy filtering by conditions
- Test chat creation, message storage, deletion
- Test context building for chat

### Task 7.2: Populate Sample Policies
**Status:** ⬜ Not Started  
**File:** `data/life-health-underwriting-policies.json`  
**Description:** Add complete policy definitions (10+) with realistic criteria

### Task 7.3: Update Existing Sample Application
**Status:** ⬜ Not Started  
**File:** `data/applications/a1b2c3d4/metadata.json`  
**Description:** Add sample `policy_citations` to LLM outputs for testing UI

### Task 7.4: Error Handling & Edge Cases
**Status:** ⬜ Not Started  
**Files:** Various  
**Description:**
- Handle missing policies gracefully
- Handle chat API errors
- Add error boundaries for chat components
- Loading states for all async operations

### Task 7.5: Print/PDF Styles for Policy Report
**Status:** ⬜ Not Started  
**File:** `frontend/src/app/globals.css`  
**Description:** Add `@media print` styles for clean PDF export

---

## Dependencies

```
Task 1.1 ──┐
           ├──► Task 1.3 ──► Task 1.4
Task 1.2 ──┘
           
Task 1.2 ──► Task 1.5 ──► Task 3.2
                 │
Task 1.4 ──► Task 1.6 ──► Task 3.2

Task 2.1 ──► Task 2.2 ──► Task 2.3 ──► Task 3.2

Task 3.1 ──► Task 3.2 ──► All Frontend Tasks

Task 4.1 ──► Task 4.2, 4.3, 4.4

Task 5.1 ──► Task 5.4
Task 5.2 ──► Task 5.3

Task 6.1, 6.2, 6.3 ──► Task 6.4 ──► Task 6.6
Task 6.5 ──► Task 6.6
```

---

## Estimated Timeline

| Phase | Description | Tasks | Est. Hours |
|-------|-------------|-------|------------|
| 1 | Backend Policy Infrastructure | 1.1-1.6 | 4-5 |
| 2 | Backend Chat Infrastructure | 2.1-2.3 | 3-4 |
| 3 | TypeScript Types & API | 3.1-3.2 | 1-2 |
| 4 | Risk Rating Popover | 4.1-4.4 | 2-3 |
| 5 | Policy Report Modal | 5.1-5.4 | 3-4 |
| 6 | Chat Slide-out Drawer | 6.1-6.6 | 4-5 |
| 7 | Testing & Polish | 7.1-7.5 | 2-3 |
| **Total** | | **30 tasks** | **19-26 hrs** |

---

## Notes

- All timestamps in ISO 8601 format (UTC)
- Chat IDs are UUIDs generated server-side
- Policy IDs follow convention: `{CATEGORY}-{SUBCATEGORY}-{NUMBER}` (e.g., `CVD-BP-001`)
- Criteria IDs append letter suffix (e.g., `CVD-BP-001-A`)
