"""
Claims Policy Engine

This module evaluates automotive claims against policy rules to determine
damage severity, liability, fraud risk, and payout recommendations.

The engine applies policy criteria from the loaded claims policies and
generates assessments with full policy citations and rationale.

Usage:
    from app.claims.policies import ClaimsPolicyLoader
    from app.claims.engine import ClaimsPolicyEngine

    loader = ClaimsPolicyLoader()
    loader.load_policies("prompts/automotive-claims-policies.json")

    engine = ClaimsPolicyEngine(loader)
    assessment = engine.evaluate_claim(claim_data)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.claims import (
    FRAUD_RISK_HIGH,
    FRAUD_RISK_LOW,
    FRAUD_RISK_MODERATE,
    LIABILITY_CLEAR,
    LIABILITY_DISPUTED,
    LIABILITY_SHARED,
    SEVERITY_HEAVY,
    SEVERITY_MINIMAL,
    SEVERITY_MINOR,
    SEVERITY_MODERATE,
    SEVERITY_TOTAL_LOSS,
)
from app.claims.policies import ClaimsPolicy, ClaimsPolicyLoader, PolicyCriterion


@dataclass
class PolicyCitation:
    """
    A citation to a specific policy rule that was applied.

    This provides traceability for how the engine reached its conclusions.
    """

    policy_id: str
    policy_name: str
    criterion_id: str
    condition: str
    action: str
    rationale: str
    # Additional context about why this rule was triggered
    match_reason: str = ""


@dataclass
class DamageAssessment:
    """Assessment of vehicle damage severity."""

    severity: str  # SEVERITY_* constant
    estimated_repair_range: tuple[float, float]  # (min, max) in dollars
    requires_senior_review: bool = False
    requires_frame_inspection: bool = False
    is_total_loss: bool = False
    damage_areas: list[dict[str, Any]] = field(default_factory=list)
    citations: list[PolicyCitation] = field(default_factory=list)
    rationale: str = ""


@dataclass
class LiabilityAssessment:
    """Assessment of liability and fault determination."""

    determination: str  # LIABILITY_* constant
    insured_fault_percentage: float  # 0-100
    other_party_fault_percentage: float  # 0-100
    requires_investigation: bool = False
    subrogation_potential: bool = False
    citations: list[PolicyCitation] = field(default_factory=list)
    rationale: str = ""


@dataclass
class FraudAssessment:
    """Assessment of fraud risk indicators."""

    risk_level: str  # FRAUD_RISK_* constant
    indicators: list[str] = field(default_factory=list)
    requires_siu_referral: bool = False
    requires_euo: bool = False  # Examination Under Oath
    citations: list[PolicyCitation] = field(default_factory=list)
    rationale: str = ""


@dataclass
class PayoutAssessment:
    """Assessment of payout recommendation."""

    estimate_status: str  # "approved", "adjusted", "requires_review"
    original_estimate: float
    recommended_payout: float
    adjustments: list[dict[str, Any]] = field(default_factory=list)
    requires_independent_appraisal: bool = False
    citations: list[PolicyCitation] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ClaimAssessment:
    """
    Complete assessment of an automotive claim.

    This combines all individual assessments (damage, liability, fraud, payout)
    into a single comprehensive assessment with policy citations.
    """

    application_id: str
    assessed_at: datetime = field(default_factory=datetime.utcnow)

    # Individual assessments
    damage: Optional[DamageAssessment] = None
    liability: Optional[LiabilityAssessment] = None
    fraud: Optional[FraudAssessment] = None
    payout: Optional[PayoutAssessment] = None

    # Overall recommendation
    overall_recommendation: str = ""  # "approve", "adjust", "deny", "investigate"
    requires_adjuster_review: bool = False
    confidence_score: float = 0.0  # 0-1

    # All policy citations across assessments
    all_citations: list[PolicyCitation] = field(default_factory=list)

    # Adjuster decision (filled in later)
    adjuster_decision: Optional[str] = None
    adjuster_notes: Optional[str] = None
    decided_at: Optional[datetime] = None


class ClaimsPolicyEngine:
    """
    Evaluates automotive claims against policy rules.

    The engine uses loaded policies to:
    - Assess damage severity based on visual evidence
    - Determine liability based on incident circumstances
    - Detect fraud indicators
    - Validate repair estimates and calculate payout recommendations

    All determinations include policy citations for transparency and audit.
    """

    # Repair estimate ranges by severity
    REPAIR_RANGES = {
        SEVERITY_MINIMAL: (0, 500),
        SEVERITY_MINOR: (0, 1000),
        SEVERITY_MODERATE: (1000, 5000),
        SEVERITY_HEAVY: (5000, 15000),
        SEVERITY_TOTAL_LOSS: (15000, float("inf")),
    }

    def __init__(self, policy_loader: ClaimsPolicyLoader) -> None:
        """
        Initialize the policy engine with a loaded policy set.

        Args:
            policy_loader: A ClaimsPolicyLoader with policies already loaded.

        Raises:
            ValueError: If the policy loader has no policies loaded.
        """
        if not policy_loader.is_loaded:
            raise ValueError("Policy loader must have policies loaded")
        self._loader = policy_loader

    def evaluate_claim(
        self,
        application_id: str,
        damage_areas: Optional[list[dict[str, Any]]] = None,
        incident_data: Optional[dict[str, Any]] = None,
        claim_history: Optional[dict[str, Any]] = None,
        repair_estimate: Optional[dict[str, Any]] = None,
    ) -> ClaimAssessment:
        """
        Perform a complete claim evaluation across all policy categories.

        Args:
            application_id: Unique identifier for the claim application.
            damage_areas: List of detected damage areas from image analysis.
            incident_data: Details about the incident for liability assessment.
            claim_history: Claimant's claims history for fraud detection.
            repair_estimate: Submitted repair estimate for payout calculation.

        Returns:
            A complete ClaimAssessment with all evaluations and citations.
        """
        assessment = ClaimAssessment(application_id=application_id)
        all_citations: list[PolicyCitation] = []

        # Evaluate damage severity
        if damage_areas:
            assessment.damage = self.evaluate_damage_severity(damage_areas)
            all_citations.extend(assessment.damage.citations)

        # Evaluate liability
        if incident_data:
            assessment.liability = self.evaluate_liability(incident_data)
            all_citations.extend(assessment.liability.citations)

        # Evaluate fraud risk
        claim_data = {
            **(claim_history or {}),
            **(incident_data or {}),
            "damage_areas": damage_areas or [],
            "repair_estimate": repair_estimate,
        }
        assessment.fraud = self.evaluate_fraud_risk(claim_data)
        all_citations.extend(assessment.fraud.citations)

        # Evaluate payout
        if repair_estimate and assessment.damage:
            assessment.payout = self.validate_estimate(
                repair_estimate, assessment.damage
            )
            all_citations.extend(assessment.payout.citations)

        # Calculate payout recommendation
        if assessment.payout is None and repair_estimate:
            payout_recommendation = self.calculate_payout_recommendation(
                repair_estimate, assessment
            )
            assessment.payout = payout_recommendation
            all_citations.extend(payout_recommendation.citations)

        assessment.all_citations = all_citations

        # Determine overall recommendation
        assessment.overall_recommendation = self._determine_overall_recommendation(
            assessment
        )
        assessment.requires_adjuster_review = self._requires_adjuster_review(assessment)
        assessment.confidence_score = self._calculate_confidence(assessment)

        return assessment

    def evaluate_damage_severity(
        self, damage_areas: list[dict[str, Any]]
    ) -> DamageAssessment:
        """
        Evaluate damage severity based on detected damage areas.

        Args:
            damage_areas: List of damage area dictionaries from image analysis.
                         Each should have keys: location, damage_type, severity,
                         estimated_cost, etc.

        Returns:
            DamageAssessment with severity rating and policy citations.
        """
        citations: list[PolicyCitation] = []
        rationale_parts: list[str] = []

        # Get damage assessment policies
        damage_policies = self._loader.get_policies_by_category("damage_assessment")

        # Analyze damage characteristics
        total_areas = len(damage_areas)
        has_structural = any(
            d.get("structural", False) or d.get("damage_type") == "structural"
            for d in damage_areas
        )
        has_airbag = any(
            "airbag" in str(d.get("component", "")).lower()
            or d.get("airbag_deployed", False)
            for d in damage_areas
        )
        total_estimated_cost = sum(
            d.get("estimated_cost", 0) or d.get("cost", 0) for d in damage_areas
        )
        severities = [d.get("severity", "Minor") for d in damage_areas]

        # Determine overall severity based on criteria
        severity = SEVERITY_MINOR
        repair_range = self.REPAIR_RANGES[SEVERITY_MINOR]
        requires_senior = False
        requires_frame = False
        is_total_loss = False

        # Find matching severity policy
        severity_policy = self._loader.get_policy_by_id("DMG-SEV-001")
        if severity_policy:
            matched_criterion = self._match_damage_severity_criterion(
                severity_policy,
                total_areas,
                has_structural,
                has_airbag,
                total_estimated_cost,
                severities,
            )
            if matched_criterion:
                severity = matched_criterion.severity or SEVERITY_MINOR
                citations.append(
                    self._create_citation(
                        severity_policy,
                        matched_criterion,
                        f"Matched based on {total_areas} damage area(s), "
                        f"structural={has_structural}, airbag={has_airbag}",
                    )
                )
                rationale_parts.append(matched_criterion.rationale)

                if severity == SEVERITY_HEAVY:
                    requires_senior = True
                    requires_frame = has_structural
                elif severity == SEVERITY_TOTAL_LOSS:
                    requires_senior = True
                    requires_frame = True
                    is_total_loss = True

        # Check damage location policies for additional context
        location_policy = self._loader.get_policy_by_id("DMG-LOC-001")
        if location_policy and damage_areas:
            for area in damage_areas:
                location = area.get("location", "").lower()
                matched = self._match_location_criterion(location_policy, location, area)
                if matched:
                    citations.append(
                        self._create_citation(
                            location_policy,
                            matched,
                            f"Location: {location}",
                        )
                    )
                    # Upgrade severity if location criterion suggests it
                    if matched.severity == SEVERITY_HEAVY and severity in [
                        SEVERITY_MINOR,
                        SEVERITY_MODERATE,
                    ]:
                        severity = SEVERITY_HEAVY
                        requires_senior = True
                        requires_frame = True

        repair_range = self.REPAIR_RANGES.get(severity, (0, 5000))

        return DamageAssessment(
            severity=severity,
            estimated_repair_range=repair_range,
            requires_senior_review=requires_senior,
            requires_frame_inspection=requires_frame,
            is_total_loss=is_total_loss,
            damage_areas=damage_areas,
            citations=citations,
            rationale=" ".join(rationale_parts),
        )

    def _match_damage_severity_criterion(
        self,
        policy: ClaimsPolicy,
        total_areas: int,
        has_structural: bool,
        has_airbag: bool,
        estimated_cost: float,
        severities: list[str],
    ) -> Optional[PolicyCriterion]:
        """Match the appropriate damage severity criterion."""
        # Check for total loss conditions
        if has_structural and estimated_cost > 10000:
            for c in policy.criteria:
                if c.severity == SEVERITY_TOTAL_LOSS:
                    return c

        # Check for heavy damage
        if has_structural or has_airbag or total_areas > 3:
            for c in policy.criteria:
                if c.severity == SEVERITY_HEAVY:
                    return c

        # Check for moderate damage
        if total_areas > 1 or any(s in ["Moderate", "moderate"] for s in severities):
            for c in policy.criteria:
                if c.severity == SEVERITY_MODERATE:
                    return c

        # Default to minor
        for c in policy.criteria:
            if c.severity == SEVERITY_MINOR:
                return c

        return None

    def _match_location_criterion(
        self, policy: ClaimsPolicy, location: str, area: dict[str, Any]
    ) -> Optional[PolicyCriterion]:
        """Match location-specific damage criteria."""
        # Map locations to criterion patterns
        location_patterns = {
            "front": ["front-end", "front", "hood", "bumper", "grille", "headlight"],
            "rear": ["rear-end", "rear", "trunk", "tailgate", "tail light"],
            "side": ["side", "door", "quarter panel", "fender"],
            "roof": ["roof", "rollover"],
        }

        for pattern_key, patterns in location_patterns.items():
            if any(p in location for p in patterns):
                # Find matching criterion
                for criterion in policy.criteria:
                    condition_lower = criterion.condition.lower()
                    if pattern_key in condition_lower:
                        # Check if severity matches damage characteristics
                        if area.get("structural") and "structural" in condition_lower:
                            return criterion
                        elif not area.get("structural") and "no" in condition_lower:
                            return criterion
                        # Return first pattern match if no specific match
                        return criterion
        return None

    def evaluate_liability(self, incident_data: dict[str, Any]) -> LiabilityAssessment:
        """
        Evaluate liability based on incident circumstances.

        Args:
            incident_data: Dictionary with incident details including:
                          - incident_type: Type of collision
                          - police_report: Whether police report exists
                          - witnesses: Number of witnesses
                          - video_evidence: Whether video evidence exists
                          - description: Incident description

        Returns:
            LiabilityAssessment with fault determination and citations.
        """
        citations: list[PolicyCitation] = []
        rationale_parts: list[str] = []

        liability_policies = self._loader.get_policies_by_category("liability")
        if not liability_policies:
            return LiabilityAssessment(
                determination=LIABILITY_DISPUTED,
                insured_fault_percentage=50.0,
                other_party_fault_percentage=50.0,
                requires_investigation=True,
                rationale="No liability policies loaded",
            )

        # Extract incident characteristics
        incident_type = incident_data.get("incident_type", "").lower()
        description = incident_data.get("description", "").lower()
        has_police_report = incident_data.get("police_report", False)
        has_video = incident_data.get("video_evidence", False)
        num_vehicles = incident_data.get("num_vehicles", 2)

        # Default values
        determination = LIABILITY_DISPUTED
        insured_fault = 50.0
        other_fault = 50.0
        requires_investigation = True
        subrogation = False

        # Find matching liability criterion
        liability_policy = self._loader.get_policy_by_id("LIA-001")
        if liability_policy:
            matched = self._match_liability_criterion(
                liability_policy, incident_type, description, num_vehicles
            )
            if matched:
                citations.append(
                    self._create_citation(
                        liability_policy, matched, f"Incident type: {incident_type}"
                    )
                )
                rationale_parts.append(matched.rationale)

                # Parse liability determination
                liability_text = (matched.liability_determination or "").lower()
                if "100% at fault" in liability_text:
                    if "following" in liability_text or "moving" in liability_text:
                        insured_fault = 0.0
                        other_fault = 100.0
                        determination = LIABILITY_CLEAR
                        subrogation = True
                    else:
                        insured_fault = 100.0
                        other_fault = 0.0
                        determination = LIABILITY_CLEAR
                elif "50/50" in liability_text or "comparative" in liability_text:
                    insured_fault = 50.0
                    other_fault = 50.0
                    determination = LIABILITY_SHARED
                elif "pending" in liability_text:
                    determination = LIABILITY_DISPUTED
                    requires_investigation = True

        # Modify based on evidence
        if has_video:
            requires_investigation = False  # Video often resolves disputes

        return LiabilityAssessment(
            determination=determination,
            insured_fault_percentage=insured_fault,
            other_party_fault_percentage=other_fault,
            requires_investigation=requires_investigation,
            subrogation_potential=subrogation,
            citations=citations,
            rationale=" ".join(rationale_parts),
        )

    def _match_liability_criterion(
        self,
        policy: ClaimsPolicy,
        incident_type: str,
        description: str,
        num_vehicles: int,
    ) -> Optional[PolicyCriterion]:
        """Match the appropriate liability criterion."""
        # Pattern matching for incident types
        patterns = {
            "rear-end": ["rear", "behind", "following"],
            "intersection": ["intersection", "signal", "light", "red light"],
            "left turn": ["left turn", "turning left"],
            "parking": ["parking", "parked"],
            "multi-vehicle": ["chain", "multiple", "pile"],
            "single": ["single", "animal", "weather", "road hazard"],
        }

        combined = f"{incident_type} {description}"

        for pattern_key, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                for criterion in policy.criteria:
                    condition_lower = criterion.condition.lower()
                    if pattern_key.replace("-", " ") in condition_lower or any(
                        kw in condition_lower for kw in keywords
                    ):
                        return criterion

        # Check multi-vehicle specifically
        if num_vehicles >= 3:
            for criterion in policy.criteria:
                if "multi" in criterion.condition.lower() or "3+" in criterion.condition:
                    return criterion

        # Return first criterion as default
        if policy.criteria:
            return policy.criteria[0]
        return None

    def evaluate_fraud_risk(self, claim_data: dict[str, Any]) -> FraudAssessment:
        """
        Evaluate fraud risk based on claim characteristics.

        Args:
            claim_data: Dictionary containing:
                       - policy_inception_date: When policy started
                       - claim_date: When claim was filed
                       - claims_history: List of prior claims
                       - repair_estimate: Submitted estimate
                       - damage_areas: Detected damage
                       - police_report: Whether report exists

        Returns:
            FraudAssessment with risk level and indicators.
        """
        citations: list[PolicyCitation] = []
        indicators: list[str] = []
        rationale_parts: list[str] = []

        fraud_policies = self._loader.get_policies_by_category("fraud_detection")
        fraud_policy = self._loader.get_policy_by_id("FRD-001")

        risk_level = FRAUD_RISK_LOW
        requires_siu = False
        requires_euo = False

        if fraud_policy:
            # Check each fraud criterion
            matched_criteria = self._check_fraud_indicators(fraud_policy, claim_data)
            for criterion, indicator in matched_criteria:
                citations.append(
                    self._create_citation(fraud_policy, criterion, indicator)
                )
                indicators.append(indicator)
                rationale_parts.append(criterion.rationale)

                # Update risk level
                criterion_risk = (criterion.risk_level or "").lower()
                if "high" in criterion_risk:
                    risk_level = FRAUD_RISK_HIGH
                    requires_siu = True
                elif "moderate" in criterion_risk and risk_level != FRAUD_RISK_HIGH:
                    risk_level = FRAUD_RISK_MODERATE

                # Check for EUO requirement
                if "euo" in (criterion.action or "").lower():
                    requires_euo = True

        # No indicators means low risk
        if not indicators:
            rationale_parts.append("No fraud indicators detected based on policy rules.")

        return FraudAssessment(
            risk_level=risk_level,
            indicators=indicators,
            requires_siu_referral=requires_siu,
            requires_euo=requires_euo,
            citations=citations,
            rationale=" ".join(rationale_parts),
        )

    def _check_fraud_indicators(
        self, policy: ClaimsPolicy, claim_data: dict[str, Any]
    ) -> list[tuple[PolicyCriterion, str]]:
        """Check for fraud indicators and return matched criteria."""
        matched: list[tuple[PolicyCriterion, str]] = []

        # Check policy inception date (FRD-001-A)
        policy_inception = claim_data.get("policy_inception_date")
        claim_date = claim_data.get("claim_date")
        if policy_inception and claim_date:
            try:
                from datetime import datetime

                if isinstance(policy_inception, str):
                    policy_inception = datetime.fromisoformat(
                        policy_inception.replace("Z", "+00:00")
                    )
                if isinstance(claim_date, str):
                    claim_date = datetime.fromisoformat(
                        claim_date.replace("Z", "+00:00")
                    )
                days_since_inception = (claim_date - policy_inception).days
                if days_since_inception <= 30:
                    for c in policy.criteria:
                        if "30 days" in c.condition:
                            matched.append(
                                (c, f"Claim filed {days_since_inception} days after policy inception")
                            )
                            break
            except (ValueError, TypeError):
                pass

        # Check estimate vs damage (FRD-001-B)
        repair_estimate = claim_data.get("repair_estimate", {})
        damage_areas = claim_data.get("damage_areas", [])
        if repair_estimate and damage_areas:
            estimate_total = repair_estimate.get("total", 0) or repair_estimate.get(
                "total_amount", 0
            )
            damage_total = sum(
                d.get("estimated_cost", 0) or d.get("cost", 0) for d in damage_areas
            )
            if damage_total > 0 and estimate_total > damage_total * 1.5:
                for c in policy.criteria:
                    if "50%" in c.condition and "estimate" in c.condition.lower():
                        matched.append(
                            (
                                c,
                                f"Estimate ${estimate_total} exceeds damage assessment ${damage_total} by {((estimate_total/damage_total)-1)*100:.0f}%",
                            )
                        )
                        break

        # Check claims history (FRD-001-C)
        claims_history = claim_data.get("claims_history", [])
        recent_claims = [
            c for c in claims_history if c.get("within_12_months", False)
        ]
        if len(recent_claims) > 2:
            for c in policy.criteria:
                if "multiple claims" in c.condition.lower() or "> 2" in c.condition:
                    matched.append(
                        (c, f"{len(recent_claims)} claims in past 12 months")
                    )
                    break

        # Check for missing police report (FRD-001-E)
        has_police_report = claim_data.get("police_report", True)
        estimate_total = (
            repair_estimate.get("total", 0)
            or repair_estimate.get("total_amount", 0)
            if repair_estimate
            else 0
        )
        if not has_police_report and estimate_total > 5000:
            for c in policy.criteria:
                if "no police report" in c.condition.lower():
                    matched.append(
                        (c, f"No police report for ${estimate_total} claim")
                    )
                    break

        return matched

    def validate_estimate(
        self, repair_estimate: dict[str, Any], damage_assessment: DamageAssessment
    ) -> PayoutAssessment:
        """
        Validate a repair estimate against the damage assessment.

        Args:
            repair_estimate: Submitted repair estimate with line items.
            damage_assessment: The damage assessment from evaluate_damage_severity.

        Returns:
            PayoutAssessment with recommendation and adjustments.
        """
        citations: list[PolicyCitation] = []
        adjustments: list[dict[str, Any]] = []
        rationale_parts: list[str] = []

        # Get payout policies
        payout_policy = self._loader.get_policy_by_id("PAY-001")

        estimate_total = repair_estimate.get("total", 0) or repair_estimate.get(
            "total_amount", 0
        )
        damage_total = sum(
            d.get("estimated_cost", 0) or d.get("cost", 0)
            for d in damage_assessment.damage_areas
        )

        # Use damage assessment range if no specific damage total
        if damage_total == 0:
            min_range, max_range = damage_assessment.estimated_repair_range
            damage_total = (min_range + min(max_range, 50000)) / 2

        # Calculate variance
        if damage_total > 0:
            variance_pct = ((estimate_total - damage_total) / damage_total) * 100
        else:
            variance_pct = 0

        status = "approved"
        recommended_payout = estimate_total
        requires_appraisal = False

        if payout_policy:
            # Find matching criterion
            if variance_pct <= 10:
                criterion = self._find_criterion_by_id(payout_policy, "PAY-001-A")
                if criterion:
                    citations.append(
                        self._create_citation(
                            payout_policy,
                            criterion,
                            f"Estimate within {variance_pct:.1f}% of assessment",
                        )
                    )
                    rationale_parts.append(criterion.rationale)
                    status = "approved"
            elif variance_pct <= 25:
                criterion = self._find_criterion_by_id(payout_policy, "PAY-001-B")
                if criterion:
                    citations.append(
                        self._create_citation(
                            payout_policy,
                            criterion,
                            f"Estimate exceeds assessment by {variance_pct:.1f}%",
                        )
                    )
                    rationale_parts.append(criterion.rationale)
                    status = "requires_review"
                    adjustments.append(
                        {
                            "type": "documentation_required",
                            "reason": "Estimate exceeds AI assessment - photo documentation needed",
                        }
                    )
            else:
                criterion = self._find_criterion_by_id(payout_policy, "PAY-001-C")
                if criterion:
                    citations.append(
                        self._create_citation(
                            payout_policy,
                            criterion,
                            f"Estimate exceeds assessment by {variance_pct:.1f}%",
                        )
                    )
                    rationale_parts.append(criterion.rationale)
                    status = "requires_review"
                    requires_appraisal = True
                    # Recommend adjusted amount
                    recommended_payout = damage_total * 1.10  # Allow 10% margin
                    adjustments.append(
                        {
                            "type": "independent_appraisal",
                            "reason": "Significant discrepancy requires third-party verification",
                            "original": estimate_total,
                            "recommended": recommended_payout,
                        }
                    )

        return PayoutAssessment(
            estimate_status=status,
            original_estimate=estimate_total,
            recommended_payout=recommended_payout,
            adjustments=adjustments,
            requires_independent_appraisal=requires_appraisal,
            citations=citations,
            rationale=" ".join(rationale_parts),
        )

    def calculate_payout_recommendation(
        self, repair_estimate: dict[str, Any], assessment: ClaimAssessment
    ) -> PayoutAssessment:
        """
        Calculate final payout recommendation considering all factors.

        Args:
            repair_estimate: The submitted repair estimate.
            assessment: The complete claim assessment so far.

        Returns:
            PayoutAssessment with final recommendation.
        """
        estimate_total = repair_estimate.get("total", 0) or repair_estimate.get(
            "total_amount", 0
        )

        # Start with estimate as base
        recommended = estimate_total
        adjustments: list[dict[str, Any]] = []
        citations: list[PolicyCitation] = []

        # Apply fraud risk adjustments
        if assessment.fraud and assessment.fraud.risk_level == FRAUD_RISK_HIGH:
            adjustments.append(
                {
                    "type": "fraud_hold",
                    "reason": "High fraud risk - payout pending investigation",
                }
            )
            return PayoutAssessment(
                estimate_status="hold",
                original_estimate=estimate_total,
                recommended_payout=0,
                adjustments=adjustments,
                requires_independent_appraisal=True,
                citations=citations,
                rationale="Payout held pending fraud investigation",
            )

        # Apply liability adjustments
        if assessment.liability:
            if assessment.liability.insured_fault_percentage > 0:
                # Reduce payout by insured's fault percentage
                fault_factor = (
                    100 - assessment.liability.insured_fault_percentage
                ) / 100
                recommended = estimate_total * fault_factor
                if fault_factor < 1:
                    adjustments.append(
                        {
                            "type": "liability_reduction",
                            "reason": f"Insured {assessment.liability.insured_fault_percentage}% at fault",
                            "reduction_pct": assessment.liability.insured_fault_percentage,
                        }
                    )

        # Apply total loss policies
        if assessment.damage and assessment.damage.is_total_loss:
            total_loss_policy = self._loader.get_policy_by_id("PAY-002")
            if total_loss_policy and total_loss_policy.criteria:
                criterion = total_loss_policy.criteria[0]
                citations.append(
                    self._create_citation(
                        total_loss_policy, criterion, "Total loss settlement"
                    )
                )
            adjustments.append(
                {
                    "type": "total_loss",
                    "reason": "Vehicle declared total loss - ACV settlement",
                }
            )

        return PayoutAssessment(
            estimate_status="approved" if not adjustments else "adjusted",
            original_estimate=estimate_total,
            recommended_payout=recommended,
            adjustments=adjustments,
            requires_independent_appraisal=False,
            citations=citations,
            rationale="Payout calculated based on estimate, liability, and policy rules",
        )

    def _find_criterion_by_id(
        self, policy: ClaimsPolicy, criterion_id: str
    ) -> Optional[PolicyCriterion]:
        """Find a specific criterion within a policy."""
        for criterion in policy.criteria:
            if criterion.id == criterion_id:
                return criterion
        return None

    def _create_citation(
        self, policy: ClaimsPolicy, criterion: PolicyCriterion, match_reason: str
    ) -> PolicyCitation:
        """Create a policy citation from a matched criterion."""
        return PolicyCitation(
            policy_id=policy.id,
            policy_name=policy.name,
            criterion_id=criterion.id,
            condition=criterion.condition,
            action=criterion.action,
            rationale=criterion.rationale,
            match_reason=match_reason,
        )

    def _determine_overall_recommendation(self, assessment: ClaimAssessment) -> str:
        """Determine the overall claim recommendation."""
        # Deny if high fraud risk
        if assessment.fraud and assessment.fraud.risk_level == FRAUD_RISK_HIGH:
            return "investigate"

        # Investigate if SIU referral required
        if assessment.fraud and assessment.fraud.requires_siu_referral:
            return "investigate"

        # Investigate if liability disputed
        if assessment.liability and assessment.liability.requires_investigation:
            return "investigate"

        # Adjust if estimate requires review
        if assessment.payout and assessment.payout.estimate_status == "requires_review":
            return "adjust"

        # Approve if everything checks out
        if assessment.payout and assessment.payout.estimate_status == "approved":
            return "approve"

        return "investigate"

    def _requires_adjuster_review(self, assessment: ClaimAssessment) -> bool:
        """Determine if adjuster review is required."""
        # Always review high-value or complex claims
        if assessment.damage and assessment.damage.requires_senior_review:
            return True
        if assessment.fraud and assessment.fraud.risk_level != FRAUD_RISK_LOW:
            return True
        if assessment.liability and assessment.liability.requires_investigation:
            return True
        if assessment.payout and assessment.payout.requires_independent_appraisal:
            return True
        return False

    def _calculate_confidence(self, assessment: ClaimAssessment) -> float:
        """Calculate confidence score for the assessment."""
        # Start with high confidence
        confidence = 1.0

        # Reduce for investigations
        if assessment.fraud and assessment.fraud.indicators:
            confidence -= 0.1 * len(assessment.fraud.indicators)

        # Reduce for disputed liability
        if assessment.liability and assessment.liability.determination == LIABILITY_DISPUTED:
            confidence -= 0.2

        # Reduce for estimate discrepancies
        if assessment.payout and assessment.payout.requires_independent_appraisal:
            confidence -= 0.15

        # Reduce for complex damage
        if assessment.damage and assessment.damage.requires_frame_inspection:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))
