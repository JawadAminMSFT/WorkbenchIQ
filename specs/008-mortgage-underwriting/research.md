# Research: Canadian Mortgage Underwriting Persona

**Feature**: 008-mortgage-underwriting  
**Date**: 2026-01-22  
**Status**: Complete

---

## Executive Summary

This document captures research findings for implementing the Canadian mortgage underwriting persona, focusing on:

1. **Regulatory requirements** - OSFI B-20 guidelines and stress testing rules
2. **Document processing** - Canadian mortgage document types and extraction
3. **Calculation methodology** - GDS/TDS/LTV formulas and OSFI MQR
4. **Existing infrastructure reuse** - Leveraging unified RAG, indexer, and policy engine patterns
5. **UX patterns** - Evidence-first workbench design per research materials

---

## OSFI B-20 Regulatory Requirements

### Minimum Qualifying Rate (MQR)

OSFI requires federally regulated financial institutions (FRFIs) to qualify uninsured mortgages at the **greater of**:

| Component | Value |
|-----------|-------|
| Contract rate + buffer | Contract rate + 2.0% |
| Floor rate | 5.25% (as of current guidance) |

**Key Points**:
- Applies to **uninsured** mortgages (LTV ≤ 80%)
- Does NOT apply to insured mortgages (CMHC/Sagen/Canada Guaranty)
- The 5.25% floor may change - OSFI announces updates as needed

### Source Reference

```yaml
sources:
  osfi_mqr_uninsured:
    description: OSFI minimum qualifying rate for uninsured mortgages
    url: https://www.osfi-bsif.gc.ca/en/supervision/financial-institutions/banks/minimum-qualifying-rate-uninsured-mortgages
```

### Implementation Note

```python
def compute_qualifying_rate(contract_rate_pct: float, settings: MortgageSettings) -> float:
    """
    Compute OSFI MQR for uninsured mortgages.
    
    Returns:
        Qualifying rate = max(contract_rate + buffer, floor)
    """
    buffer = settings.osfi_mqr_buffer_pct  # Default: 2.0
    floor = settings.osfi_mqr_floor_pct    # Default: 5.25
    
    return max(contract_rate_pct + buffer, floor)
```

---

## Debt Service Ratio Calculations

### GDS (Gross Debt Service) Formula

```
GDS = (P&I + Taxes + Heating + 50% Condo Fees) / Gross Monthly Income
```

Where:
- **P&I** = Monthly principal and interest payment
- **Taxes** = Monthly property taxes (annual / 12)
- **Heating** = Monthly heating cost estimate
- **Condo Fees** = 50% of monthly condo/strata fees (lender-specific)

### TDS (Total Debt Service) Formula

```
TDS = (P&I + Taxes + Heating + 50% Condo Fees + Other Debts) / Gross Monthly Income
```

Where:
- **Other Debts** = Credit card minimums, car loans, student loans, support payments, etc.

### Mortgage Payment Calculation

Standard amortization formula:

```
P&I = P × [r(1+r)^n] / [(1+r)^n - 1]
```

Where:
- **P** = Principal (loan amount)
- **r** = Monthly interest rate (annual rate / 12)
- **n** = Total number of payments (amortization months)

### Python Implementation

```python
def compute_mortgage_payment(
    principal: float,
    annual_rate_pct: float,
    amortization_months: int
) -> float:
    """
    Compute monthly P&I payment using standard amortization formula.
    """
    if annual_rate_pct == 0:
        return principal / amortization_months
    
    monthly_rate = annual_rate_pct / 100 / 12
    n = amortization_months
    
    payment = principal * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)
    return round(payment, 2)
```

---

## LTV (Loan-to-Value) Rules

### Canadian LTV Categories

| LTV Range | Category | Requirements |
|-----------|----------|--------------|
| ≤ 65% | Low LTV | Standard underwriting |
| 65% - 80% | Conventional | Standard underwriting, no insurance |
| 80% - 95% | High Ratio | Mortgage insurance required |
| > 95% | Not permitted | Cannot exceed 95% LTV in Canada |

### Combined LTV

When secondary financing exists (HELOC, second mortgage):

```
Combined LTV = (First Mortgage + Secondary Financing) / Property Value
```

---

## Canadian Mortgage Document Types

### Document Classification Matrix

| Document Type | Key Fields | Confidence Priority | Notes |
|---------------|------------|---------------------|-------|
| `application_summary` | Borrower info, requested amount, property | High | Central intake form |
| `employment_letter` | Employer, position, salary, start date | High | Must be dated within 30 days |
| `pay_stub` | Gross pay, period, YTD | High | Recent (within 30 days) |
| `t4` | Employment income (Box 14), employer | High | Primary income verification |
| `notice_of_assessment` | Total income, tax year | High | CRA confirmation |
| `bank_statement` | Balances, transactions, deposits | Medium | 3 months typically required |
| `gift_letter` | Donor, amount, relationship | High | Must state "no repayment" |
| `purchase_sale_agreement` | Price, property, conditions, closing | High | Firm/conditional status |
| `appraisal_report` | Value, property type, as-of date | High | Within 90 days |
| `credit_report` | Score, trades, delinquencies | High | Pulled at application |

### Document Type Detection Heuristics

```python
DOCUMENT_TYPE_KEYWORDS = {
    "employment_letter": ["employment", "confirm", "employer", "salary", "position"],
    "pay_stub": ["pay stub", "pay statement", "earnings statement", "gross pay"],
    "t4": ["t4", "statement of remuneration", "employment income", "box 14"],
    "notice_of_assessment": ["notice of assessment", "noa", "cra", "canada revenue"],
    "bank_statement": ["account statement", "bank statement", "transaction history"],
    "gift_letter": ["gift letter", "gift declaration", "gifted funds"],
    "purchase_sale_agreement": ["agreement of purchase", "purchase agreement", "aps"],
    "appraisal_report": ["appraisal", "valuation report", "market value estimate"],
    "credit_report": ["credit report", "credit bureau", "equifax", "transunion"],
}
```

---

## Income Qualification Rules

### Salaried/Hourly Income

- Use gross annual salary from employment letter or T4
- Pay stub YTD can verify current employment
- Probationary period income may be reduced or excluded

### Variable Income (Bonus, Commission, Overtime)

| Income Type | Typical Haircut | Documentation |
|-------------|-----------------|---------------|
| Bonus | 50% of 2-year average | T4s + employment letter |
| Commission | 50% of 2-year average | T4s + T1 General |
| Overtime | 50% of 2-year average | Pay stubs + T4 |

### Self-Employed Income

- Use 2-year average of net business income from T1 General
- NOA confirms filed income
- Business financials may be required for add-backs

### Rental Income

- Use 50% of gross rental income
- OR 100% less vacancy/management factor (lender-specific)
- Offset against property expenses if existing rental

### Implementation

```python
def compute_monthly_income(
    income_sources: list[IncomeSource],
    haircut_rules: dict[str, float]
) -> MonthlyIncomeResult:
    """
    Compute qualifying monthly income with haircuts.
    """
    total = 0.0
    breakdown = []
    
    for source in income_sources:
        haircut = haircut_rules.get(source.income_type, 1.0)
        annual = source.annual_amount
        qualifying_annual = annual * haircut
        qualifying_monthly = qualifying_annual / 12
        
        breakdown.append({
            "borrowerId": source.borrower_id,
            "type": source.income_type,
            "annualAmount": annual,
            "haircut": haircut,
            "qualifyingMonthly": qualifying_monthly,
            "source": source.provenance,
        })
        total += qualifying_monthly
    
    return MonthlyIncomeResult(
        value=round(total, 2),
        breakdown=breakdown,
    )

DEFAULT_HAIRCUTS = {
    "base_salary": 1.0,
    "hourly": 1.0,
    "bonus": 0.5,
    "commission": 0.5,
    "overtime": 0.5,
    "rental": 0.5,
    "self_employed_net": 1.0,  # Already averaged
}
```

---

## Existing Infrastructure Reuse

### 1. Unified RAG Service

The mortgage persona integrates with `app/rag/service.py`:

```python
# Location: app/rag/service.py

class RAGService:
    def __init__(
        self,
        settings: Settings | None = None,
        max_context_tokens: int = 4000,
        use_hybrid_search: bool = True,
        persona: str = "underwriting",  # Add: "mortgage_underwriting"
    ):
```

**Integration Point**: Pass `persona="mortgage_underwriting"` to get mortgage-specific policy search.

### 2. Unified Indexer

Add mortgage persona to `app/rag/unified_indexer.py`:

```python
# Location: app/rag/unified_indexer.py

PERSONA_CONFIG = {
    "underwriting": {...},
    "life_health_claims": {...},
    "automotive_claims": {...},
    "property_casualty_claims": {...},
    # NEW:
    "mortgage_underwriting": {
        "policies_path": "prompts/mortgage-underwriting-policies.json",
        "table_name": "mortgage_policy_chunks",
        "display_name": "Mortgage Underwriting",
    },
}
```

### 3. Policy Engine Pattern

Adapt from `app/claims/engine.py`:

```python
# Existing pattern in app/claims/engine.py

@dataclass
class PolicyCitation:
    policy_id: str
    policy_name: str
    criterion_id: str
    condition: str
    action: str
    rationale: str
    match_reason: str = ""

@dataclass
class ClaimAssessment:
    damage_assessment: DamageAssessment
    liability_assessment: LiabilityAssessment
    fraud_assessment: FraudAssessment
    payout_assessment: PayoutAssessment
```

**Adapt for Mortgage**:

```python
# New pattern in app/mortgage/engine.py

@dataclass
class PolicyCitation:
    """Same structure, reusable"""
    pass

@dataclass
class MortgageAssessment:
    calculations: CalculationResult
    policy_findings: list[PolicyFinding]
    risk_assessment: RiskAssessment
    recommendation: DecisionRecommendation
```

### 4. Policy Loader Pattern

Adapt from `app/claims/policies.py`:

```python
# Existing pattern
class ClaimsPolicyLoader:
    def load_policies(self, path: str) -> list[ClaimsPolicy]:
        ...
    
    def get_policies_by_category(self, category: str) -> list[ClaimsPolicy]:
        ...
```

**Adapt for Mortgage**:

```python
# New in app/mortgage/policies.py
class MortgagePolicyLoader:
    def load_policies(self, path: str) -> list[MortgagePolicy]:
        ...
    
    def get_osfi_rules(self) -> list[MortgagePolicy]:
        return self.get_policies_by_category("osfi_regulatory")
```

### 5. Persona Configuration

Extend `app/personas.py`:

```python
# Existing enum
class PersonaType(str, Enum):
    UNDERWRITING = "underwriting"
    LIFE_HEALTH_CLAIMS = "life_health_claims"
    AUTOMOTIVE_CLAIMS = "automotive_claims"
    MORTGAGE = "mortgage"  # Existing stub
    # NEW:
    MORTGAGE_UNDERWRITING = "mortgage_underwriting"
```

### 6. Content Understanding Client

Extend `app/content_understanding_client.py` for mortgage analyzer:

```python
# Add analyzer creation/usage for mortgageDocAnalyzer
async def analyze_mortgage_document(
    file_bytes: bytes,
    filename: str,
    doc_type: str,
    settings: Settings,
) -> MortgageAnalysisResult:
    """
    Analyze a mortgage document using the custom analyzer.
    """
    client = ContentUnderstandingClient(settings)
    
    result = await client.analyze(
        analyzer_id=settings.mortgage_doc_analyzer,
        file_bytes=file_bytes,
        filename=filename,
    )
    
    return MortgageAnalysisResult.from_cu_response(result, doc_type)
```

---

## UX Research: Underwriter Workbench

Based on `mortgage-research/underwriter_workbench_ux_spec.md`:

### 3-Column Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UNDERWRITER WORKBENCH                                │
├────────────────┬────────────────────────────────┬──────────────────────────┤
│  LEFT (25%)    │       CENTER (50%)              │     RIGHT (25%)          │
│                │                                  │                          │
│  EVIDENCE      │  DATA + POLICY TABS              │  RISK + NARRATIVE        │
│                │                                  │                          │
│  • Doc groups  │  Tab A: Data Worksheet           │  • Risk tier badge       │
│    - Identity  │  • Canonical data tree           │  • Top contributors      │
│    - Income    │  • Field with provenance         │                          │
│    - Assets    │  • Conflict resolver             │  • Fraud/AML signals     │
│    - Property  │                                  │                          │
│    - Credit    │  Tab B: Calculations             │  • AI underwriting note  │
│                │  • GDS/TDS table                 │    (editable)            │
│  • Doc viewer  │  • Stress test toggle            │                          │
│    - Pages     │  • Input provenance              │  • "What would change    │
│    - Search    │                                  │    the decision?"        │
│    - Highlight │  Tab C: Policy Checks            │                          │
│                │  • Rule list with status         │                          │
│                │  • Rule detail drawer            │                          │
│                │  • Exception workflow            │                          │
│                │                                  │                          │
│                │  Tab D: Conditions               │                          │
│                │  • Auto-generated stips          │                          │
│                │  • Send to borrower/broker       │                          │
└────────────────┴────────────────────────────────┴──────────────────────────┘
│                            DECISION CONTROLS                                 │
│  [Approve]  [Refer]  [Decline]  [Pending Info]     Conditions: [✓] [✓] [✓]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key UX Components

1. **Provenance Chip**: Hover shows documentId/page/bounding region + extractor + timestamp
2. **Conflict Resolver**: Side-by-side values + "select winner" + required note
3. **Explain-this Drawer**: Expands any calc/rule into inputs → formula → output
4. **Risk Tier Badge**: Color-coded (green/yellow/orange/red) with top contributors

### Decision Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Review    │────▶│   Resolve   │────▶│   Decide    │────▶│   Lock      │
│   Evidence  │     │   Conflicts │     │   + Note    │     │   Snapshot  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Risk Analysis Patterns

### Income Consistency Check

```python
def check_income_consistency(
    t4_income: float,
    pay_stub_income: float,
    application_income: float,
    threshold_pct: float = 0.05,
) -> IncomeConsistencyResult:
    """
    Check if income reported across sources is consistent.
    """
    sources = [t4_income, pay_stub_income, application_income]
    valid_sources = [s for s in sources if s and s > 0]
    
    if len(valid_sources) < 2:
        return IncomeConsistencyResult(
            consistent=True,
            variance_pct=0,
            note="Insufficient sources to compare",
        )
    
    max_income = max(valid_sources)
    min_income = min(valid_sources)
    variance_pct = (max_income - min_income) / max_income
    
    return IncomeConsistencyResult(
        consistent=variance_pct <= threshold_pct,
        variance_pct=variance_pct,
        max_source=max_income,
        min_source=min_income,
        note=f"Variance: {variance_pct:.1%}",
    )
```

### Fraud Red Flags

Based on `canadian_underwriting_decisioning_manual.md`:

| Red Flag | Detection Method |
|----------|------------------|
| Document alterations | Font inconsistency, metadata anomalies |
| Large unexplained deposits | Bank statement analysis, threshold check |
| Employer verification failure | Directory lookup, contact verification |
| Address/identity mismatch | Cross-doc comparison |
| Recent address changes | Credit bureau history analysis |
| Thin credit with large exposure | Score vs. loan amount ratio |

---

## Policy Rule Categories

### Mapping from YAML Catalog

```yaml
# From canada_underwriting_rules_catalog.yaml

rules:
- ruleId: CA.OSFI.MQR.UNINSURED          # → osfi_regulatory
- ruleId: CA.UW.DSR.GDS_TDS              # → income_qualification
- ruleId: CA.UW.COLLATERAL.LTV           # → collateral_valuation
- ruleId: CA.UW.DP.SOURCE_OF_FUNDS       # → down_payment
- ruleId: CA.UW.INCOME.CONSISTENCY       # → income_qualification
- ruleId: CA.UW.AML.RED_FLAGS            # → aml_fraud
```

### Category Hierarchy

```
mortgage_underwriting_policies
├── osfi_regulatory
│   ├── stress_test (MQR)
│   └── portfolio_limits
├── credit_evaluation
│   ├── bureau_score
│   ├── delinquencies
│   └── utilization
├── income_qualification
│   ├── debt_service (GDS/TDS)
│   ├── verification
│   └── stability
├── collateral_valuation
│   ├── ltv_limits
│   └── property_eligibility
├── down_payment
│   ├── minimum_required
│   └── source_verification
├── aml_fraud
│   ├── aml_triage
│   └── fraud_indicators
└── documentation
    └── completeness
```

---

## Sample Policy JSON Structure

```json
{
  "version": "1.0",
  "jurisdiction": "CA",
  "effective_date": "2026-01-01",
  "description": "Canadian Mortgage Underwriting Policies - OSFI B-20 Aligned",
  "sources": {
    "osfi_b20": {
      "description": "OSFI Guideline B-20 - Residential Mortgage Underwriting",
      "url": "https://www.osfi-bsif.gc.ca/..."
    }
  },
  "policies": [
    {
      "id": "CA.OSFI.MQR.UNINSURED",
      "category": "osfi_regulatory",
      "subcategory": "stress_test",
      "name": "Uninsured Mortgage Qualifying Rate",
      "description": "...",
      "criteria": [
        {
          "id": "CA.OSFI.MQR.UNINSURED-A",
          "condition": "...",
          "action": "...",
          "severity": "critical",
          "rationale": "..."
        }
      ],
      "inputs": [
        {"name": "contractRatePct", "path": "loan.contractRatePct"},
        {"name": "floorPct", "value": 5.25}
      ],
      "outputs": ["calculations.stressTest.qualifyingRatePct"]
    }
  ]
}
```

---

## Integration Testing Strategy

### Sample Test Data

Use `mortgage-research/canadian_mortgage_sample_package/`:

- `bundle_manifest.json` - Document list
- `bundle_ground_truth.json` - Expected extracted values

### Test Cases

| Test Case | Description | Expected |
|-----------|-------------|----------|
| TC-001 | Process complete package | All docs classified correctly |
| TC-002 | Compute GDS/TDS | Match ground truth within 0.1% |
| TC-003 | Apply MQR stress test | Qualifying rate = max(5.25%, 7.25%) |
| TC-004 | Detect income inconsistency | Flag if >5% variance |
| TC-005 | LTV > 80% conventional | Fail with insurance required |
| TC-006 | Down payment unverified | needs_review status |

---

## References

- [OSFI Guideline B-20](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-b-20)
- [OSFI Minimum Qualifying Rate](https://www.osfi-bsif.gc.ca/en/supervision/financial-institutions/banks/minimum-qualifying-rate-uninsured-mortgages)
- [Spec 007: Automotive Claims](../007-automotive-claims-multimodal/spec.md) - Architecture pattern reference
- [mortgage-research/](../../../mortgage-research/) - Domain research materials
