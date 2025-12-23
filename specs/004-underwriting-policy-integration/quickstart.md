# Spec 004: Quick Implementation Guide

## Pre-Implementation Checklist

Before starting implementation, verify:

- [ ] Existing `data/policies.json` is for claims (different from new underwriting policies)
- [ ] `app/processing.py` has `_run_single_prompt()` that accepts `additional_context`
- [ ] `frontend/src/components/PatientSummary.tsx` has "Recommended Action" section to replace
- [ ] `frontend/src/lib/types.ts` has `ParsedOutput` interface to extend
- [ ] `specs/` folder exists for tracking (✅ confirmed)

## Implementation Order (Recommended)

### Day 1: Backend Foundation
1. **Task 1.1** - Create `life-health-underwriting-policies.json` (start with 5 policies)
2. **Task 1.2** - Create `app/underwriting_policies.py`
3. **Task 1.5** - Add `GET /api/underwriting-policies` endpoint
4. **Task 3.1** - Add TypeScript types for policies

### Day 2: Policy Integration
5. **Task 1.3** - Update prompt templates with policy citation requirements
6. **Task 1.4** - Modify processing.py to inject policies
7. **Task 1.6** - Add `POST /api/applications/{id}/run-policy-check`
8. **Task 3.2** - Add API client methods (policy-related)

### Day 3: Risk Popover & Report
9. **Task 4.1** - Create `RiskRatingPopover.tsx`
10. **Task 4.2-4.4** - Integrate popover into existing components
11. **Task 5.1** - Create `PolicyReportModal.tsx`
12. **Task 5.2** - Create `PolicySummaryPanel.tsx`
13. **Task 5.3-5.4** - Integrate into PatientSummary and page

### Day 4: Chat Backend
14. **Task 2.1** - Create `app/chat_storage.py`
15. **Task 2.2** - Create `app/chat_service.py`
16. **Task 2.3** - Add chat API endpoints
17. **Task 3.2** - Add API client methods (chat-related)

### Day 5: Chat Frontend
18. **Task 6.1** - Create `ChatMessage.tsx`
19. **Task 6.2** - Create `ChatWindow.tsx`
20. **Task 6.3** - Create `ChatList.tsx`
21. **Task 6.4** - Create `ChatDrawer.tsx`
22. **Task 6.5** - Create `ChatContext.tsx`
23. **Task 6.6** - Integrate into main page

### Day 6: Polish
24. **Task 7.1-7.5** - Testing, sample data, error handling, PDF styles

## Key Integration Points

### Backend: `app/processing.py`
```python
# In _run_single_prompt(), add policy injection:
from .underwriting_policies import load_policies, format_policies_for_prompt

def _run_single_prompt(..., additional_context: str = ""):
    # Load and inject policies
    policies = load_policies(settings.app.storage_root)
    policy_context = format_policies_for_prompt(policies)
    
    user_prompt = prompt_template.strip() + "\n\n---\n\n"
    user_prompt += "UNDERWRITING POLICIES:\n" + policy_context + "\n\n---\n\n"
    user_prompt += "Application Markdown:\n\n" + document_markdown
```

### Frontend: Risk Badge Replacement
```tsx
// Before (PatientSummary.tsx):
<span className="px-3 py-1 rounded-full...">{riskAssessment}</span>

// After:
<RiskRatingPopover
  riskLevel={riskAssessment}
  rationale={customerProfile?.risk_rationale}
  policyCitations={customerProfile?.policy_citations}
>
  <span className="px-3 py-1 rounded-full...">{riskAssessment}</span>
</RiskRatingPopover>
```

### Frontend: Recommended Action Replacement
```tsx
// Before:
{underwritingAction && (
  <div className="pt-3 border-t border-slate-100">
    <h4 className="text-xs font-medium...">Recommended Action</h4>
    <p className="text-sm...">{underwritingAction}</p>
  </div>
)}

// After:
<PolicySummaryPanel 
  application={application}
  onViewFullReport={() => setShowPolicyModal(true)}
/>
```

## Testing Strategy

1. **Manual Test Flow:**
   - Load existing application (a1b2c3d4)
   - Verify popover appears on hover (may show "no citation" initially)
   - Run "Policy Check" → verify modal shows
   - Export PDF → verify clean output
   - Open chat → send message → verify response with context
   - Switch application → verify new chat session

2. **Re-run Analysis:**
   - After implementing policy injection, re-run analysis on sample application
   - Verify new outputs contain `risk_rationale` and `policy_citations`

## Rollback Plan

If issues arise:
- Policy injection can be disabled by removing `additional_context` parameter
- Chat drawer can be hidden with feature flag
- PopoverRating falls back gracefully to simple badge if no citations

## Success Metrics

- [ ] All risk badges show popover on hover
- [ ] Policy report modal displays with PDF export working
- [ ] Chat responds with policy-aware answers
- [ ] Chat history persists across page refreshes
- [ ] Switching applications creates new chat session
