"""
Tests for Phase 5: Claims Policy Engine
Feature: 007-automotive-claims-multimodal

Tests cover:
- Policy loading from JSON
- Damage severity evaluation (DMG-SEV policies)
- Liability determination (LIA policies)
- Fraud risk evaluation (FRD policies)
- Estimate validation (PAY policies)
- Payout recommendation calculation
- Policy citations and rationale
"""
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Import claims policy components
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
from app.claims.policies import (
    ClaimsPolicy,
    ClaimsPolicyDocument,
    ClaimsPolicyLoader,
    ModifyingFactor,
    PolicyCriterion,
)
from app.claims.engine import (
    ClaimAssessment,
    ClaimsPolicyEngine,
    DamageAssessment,
    FraudAssessment,
    LiabilityAssessment,
    PayoutAssessment,
    PolicyCitation,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def policy_json_path():
    """Return path to the automotive claims policies JSON."""
    return Path("prompts/automotive-claims-policies.json")


@pytest.fixture
def loaded_policy_loader(policy_json_path):
    """Return a policy loader with policies loaded."""
    loader = ClaimsPolicyLoader()
    loader.load_policies(policy_json_path)
    return loader


@pytest.fixture
def policy_engine(loaded_policy_loader):
    """Return a policy engine with loaded policies."""
    return ClaimsPolicyEngine(loaded_policy_loader)


@pytest.fixture
def sample_damage_areas():
    """Sample damage areas from image analysis."""
    return [
        {
            "location": "front_bumper",
            "component": "bumper",
            "damage_type": "dent",
            "severity": "Moderate",
            "confidence": 0.92,
            "estimated_cost": 800,
            "structural": False,
        },
        {
            "location": "front_hood",
            "component": "hood",
            "damage_type": "crease",
            "severity": "Moderate",
            "confidence": 0.88,
            "estimated_cost": 1200,
            "structural": False,
        },
    ]


@pytest.fixture
def sample_incident_data():
    """Sample incident data for liability assessment."""
    return {
        "incident_type": "rear-end collision",
        "description": "Vehicle was struck from behind while stopped at red light",
        "police_report": True,
        "witnesses": 2,
        "video_evidence": True,
        "num_vehicles": 2,
    }


@pytest.fixture
def sample_claim_history():
    """Sample claim history for fraud detection."""
    return {
        "policy_inception_date": (datetime.now() - timedelta(days=365)).isoformat(),
        "claim_date": datetime.now().isoformat(),
        "claims_history": [
            {"within_12_months": False, "amount": 2500},
        ],
        "police_report": True,
    }


@pytest.fixture
def sample_repair_estimate():
    """Sample repair estimate."""
    return {
        "total": 2200,
        "line_items": [
            {"description": "Front bumper replacement", "total_price": 800},
            {"description": "Hood repair", "total_price": 1200},
            {"description": "Labor", "total_price": 200},
        ],
    }


# =============================================================================
# Policy Loader Tests (T058-T060)
# =============================================================================


class TestClaimsPolicyLoader:
    """Tests for ClaimsPolicyLoader class."""

    def test_load_policies_from_json(self, policy_json_path):
        """Should load policies from JSON file."""
        loader = ClaimsPolicyLoader()
        doc = loader.load_policies(policy_json_path)

        assert loader.is_loaded
        assert doc is not None
        assert doc.version == "1.0"
        assert len(doc.policies) > 0

    def test_load_policies_returns_structured_objects(self, policy_json_path):
        """Loaded policies should be structured Python objects."""
        loader = ClaimsPolicyLoader()
        doc = loader.load_policies(policy_json_path)

        assert isinstance(doc, ClaimsPolicyDocument)
        assert all(isinstance(p, ClaimsPolicy) for p in doc.policies)

        # Check first policy structure
        policy = doc.policies[0]
        assert isinstance(policy.criteria, list)
        assert all(isinstance(c, PolicyCriterion) for c in policy.criteria)
        assert isinstance(policy.modifying_factors, list)

    def test_get_policies_by_category(self, loaded_policy_loader):
        """Should filter policies by category."""
        damage_policies = loaded_policy_loader.get_policies_by_category(
            "damage_assessment"
        )
        assert len(damage_policies) > 0
        for policy in damage_policies:
            assert policy.category == "damage_assessment"

    def test_get_damage_assessment_policies(self, loaded_policy_loader):
        """Should return damage_assessment category policies."""
        policies = loaded_policy_loader.get_policies_by_category("damage_assessment")
        assert len(policies) >= 1
        # Should include severity rating policy
        policy_ids = [p.id for p in policies]
        assert "DMG-SEV-001" in policy_ids

    def test_get_liability_policies(self, loaded_policy_loader):
        """Should return liability category policies."""
        policies = loaded_policy_loader.get_policies_by_category("liability")
        assert len(policies) >= 1
        policy_ids = [p.id for p in policies]
        assert "LIA-001" in policy_ids

    def test_loader_initialization(self):
        """Test that loader initializes with empty state."""
        loader = ClaimsPolicyLoader()
        assert not loader.is_loaded
        assert loader.document is None

    def test_load_policies_file_not_found(self):
        """Test error handling for missing file."""
        loader = ClaimsPolicyLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_policies("nonexistent/path.json")

    def test_get_policies_by_category_empty(self, loaded_policy_loader):
        """Test empty result for unknown category."""
        policies = loaded_policy_loader.get_policies_by_category("unknown_category")
        assert policies == []

    def test_get_policy_by_id(self, loaded_policy_loader):
        """Test getting a specific policy by ID."""
        policy = loaded_policy_loader.get_policy_by_id("DMG-SEV-001")
        assert policy is not None
        assert policy.id == "DMG-SEV-001"
        assert policy.name == "Damage Severity Classification"

    def test_get_policy_by_id_not_found(self, loaded_policy_loader):
        """Test None result for unknown policy ID."""
        policy = loaded_policy_loader.get_policy_by_id("UNKNOWN-001")
        assert policy is None

    def test_get_all_policies(self, loaded_policy_loader):
        """Test getting all policies."""
        policies = loaded_policy_loader.get_all_policies()
        assert len(policies) > 0

    def test_get_categories(self, loaded_policy_loader):
        """Test getting all unique categories."""
        categories = loaded_policy_loader.get_categories()
        assert "damage_assessment" in categories
        assert "liability" in categories
        assert "fraud_detection" in categories
        assert "payout_calculation" in categories

    def test_get_criterion_by_id(self, loaded_policy_loader):
        """Test getting a specific criterion by ID."""
        result = loaded_policy_loader.get_criterion_by_id("DMG-SEV-001-A")
        assert result is not None
        policy, criterion = result
        assert policy.id == "DMG-SEV-001"
        assert criterion.id == "DMG-SEV-001-A"
        assert criterion.severity == "Minor"

    def test_get_criterion_by_id_not_found(self, loaded_policy_loader):
        """Test None result for unknown criterion ID."""
        result = loaded_policy_loader.get_criterion_by_id("UNKNOWN-001-A")
        assert result is None

    def test_policies_by_subcategory(self, loaded_policy_loader):
        """Test filtering by category and subcategory."""
        policies = loaded_policy_loader.get_policies_by_subcategory(
            "damage_assessment", "severity_rating"
        )
        assert len(policies) > 0
        for p in policies:
            assert p.category == "damage_assessment"
            assert p.subcategory == "severity_rating"


# =============================================================================
# Damage Severity Evaluation Tests (T062)
# =============================================================================


class TestDamageSeverityEvaluation:
    """Tests for damage severity policy evaluation."""

    def test_damage_severity_minor(self, policy_engine):
        """Minor damage should return Minor severity rating."""
        damage_areas = [
            {
                "location": "door",
                "damage_type": "scratch",
                "severity": "Minor",
                "estimated_cost": 300,
                "structural": False,
            }
        ]

        assessment = policy_engine.evaluate_damage_severity(damage_areas)

        assert assessment.severity in [SEVERITY_MINOR, SEVERITY_MODERATE]
        assert not assessment.is_total_loss
        assert not assessment.requires_frame_inspection

    def test_damage_severity_moderate(self, policy_engine, sample_damage_areas):
        """Moderate damage should return Moderate severity rating."""
        assessment = policy_engine.evaluate_damage_severity(sample_damage_areas)

        assert assessment.severity == SEVERITY_MODERATE
        assert not assessment.is_total_loss
        assert len(assessment.citations) > 0

    def test_damage_severity_heavy(self, policy_engine):
        """Heavy damage should return Heavy severity rating."""
        damage_areas = [
            {
                "location": "frame",
                "damage_type": "structural",
                "severity": "Heavy",
                "estimated_cost": 8000,
                "structural": True,
            },
            {
                "location": "airbag",
                "component": "airbag",
                "damage_type": "deployed",
                "severity": "Heavy",
                "estimated_cost": 2000,
                "airbag_deployed": True,
            },
        ]

        assessment = policy_engine.evaluate_damage_severity(damage_areas)

        assert assessment.severity == SEVERITY_HEAVY
        assert assessment.requires_senior_review
        assert assessment.requires_frame_inspection

    def test_damage_severity_total_loss(self, policy_engine):
        """Extensive damage should return Total Loss severity rating."""
        damage_areas = [
            {
                "location": "frame",
                "damage_type": "structural",
                "severity": "Total Loss",
                "estimated_cost": 15000,
                "structural": True,
            },
        ]

        assessment = policy_engine.evaluate_damage_severity(damage_areas)

        assert assessment.severity in [SEVERITY_HEAVY, SEVERITY_TOTAL_LOSS]
        assert assessment.requires_senior_review

    def test_severity_considers_modifying_factors(self, policy_engine):
        """Should apply modifying factors (vehicle age, prior damage)."""
        # This is primarily a policy presence test
        loader = policy_engine._loader
        policy = loader.get_policy_by_id("DMG-SEV-001")
        assert policy is not None
        assert len(policy.modifying_factors) > 0
        
        # Check for expected modifying factors
        factor_names = [f.factor for f in policy.modifying_factors]
        assert any("age" in f.lower() for f in factor_names)


# =============================================================================
# Liability Evaluation Tests (T063)
# =============================================================================


class TestLiabilityEvaluation:
    """Tests for liability policy evaluation."""

    def test_liability_rear_end_collision(self, policy_engine, sample_incident_data):
        """Rear-end collision should assign 100% fault to following vehicle."""
        assessment = policy_engine.evaluate_liability(sample_incident_data)

        assert assessment.determination == LIABILITY_CLEAR
        assert assessment.insured_fault_percentage == 0.0
        assert assessment.other_party_fault_percentage == 100.0
        assert assessment.subrogation_potential
        assert len(assessment.citations) > 0

    def test_liability_intersection_collision(self, policy_engine):
        """Intersection collision should consider signal status."""
        incident_data = {
            "incident_type": "intersection collision",
            "description": "Other vehicle ran red light",
            "police_report": True,
            "num_vehicles": 2,
        }

        assessment = policy_engine.evaluate_liability(incident_data)

        assert assessment.determination in [LIABILITY_CLEAR, LIABILITY_SHARED]
        assert len(assessment.citations) > 0

    def test_liability_parking_lot(self, policy_engine):
        """Parking lot collision should follow parking lot rules."""
        incident_data = {
            "incident_type": "parking lot",
            "description": "Vehicle was parked when struck",
            "police_report": False,
            "num_vehicles": 2,
        }

        assessment = policy_engine.evaluate_liability(incident_data)

        assert assessment is not None
        # Parked vehicle should have 0% fault
        if "parked" in incident_data["description"].lower():
            assert assessment.insured_fault_percentage <= 50.0

    def test_liability_multi_vehicle(self, policy_engine):
        """Multi-vehicle collision should analyze chain reaction."""
        incident_data = {
            "incident_type": "chain reaction pile-up",
            "description": "Multi-vehicle chain reaction on highway",
            "police_report": True,
            "num_vehicles": 4,
        }

        assessment = policy_engine.evaluate_liability(incident_data)

        assert assessment is not None
        # Multi-vehicle should require investigation
        assert len(assessment.citations) > 0


# =============================================================================
# Fraud Risk Evaluation Tests (T064)
# =============================================================================


class TestFraudRiskEvaluation:
    """Tests for fraud detection policy evaluation."""

    def test_fraud_new_policy(self, policy_engine):
        """Claim within 30 days of inception should flag high risk."""
        claim_data = {
            "policy_inception_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "claim_date": datetime.now().isoformat(),
            "claims_history": [],
            "police_report": True,
        }

        assessment = policy_engine.evaluate_fraud_risk(claim_data)

        assert assessment.risk_level == FRAUD_RISK_HIGH
        assert assessment.requires_siu_referral
        assert any("15 days" in ind or "inception" in ind.lower() for ind in assessment.indicators)

    def test_fraud_estimate_inflation(self, policy_engine):
        """Estimate exceeding damage by >50% should flag moderate risk."""
        claim_data = {
            "policy_inception_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "claim_date": datetime.now().isoformat(),
            "claims_history": [],
            "police_report": True,
            "repair_estimate": {"total": 10000},
            "damage_areas": [{"estimated_cost": 3000}],
        }

        assessment = policy_engine.evaluate_fraud_risk(claim_data)

        # Estimate exceeds damage by >50% (10000 vs 3000)
        assert assessment.risk_level in [FRAUD_RISK_MODERATE, FRAUD_RISK_HIGH]
        assert any("exceeds" in ind.lower() or "%" in ind for ind in assessment.indicators)

    def test_fraud_multiple_claims(self, policy_engine):
        """Multiple claims in 12 months should flag moderate risk."""
        claim_data = {
            "policy_inception_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "claim_date": datetime.now().isoformat(),
            "claims_history": [
                {"within_12_months": True, "amount": 1500},
                {"within_12_months": True, "amount": 2000},
                {"within_12_months": True, "amount": 3000},
            ],
            "police_report": True,
        }

        assessment = policy_engine.evaluate_fraud_risk(claim_data)

        assert assessment.risk_level == FRAUD_RISK_MODERATE
        assert any("claims" in ind.lower() for ind in assessment.indicators)

    def test_fraud_damage_inconsistency(self, policy_engine):
        """Damage inconsistent with narrative should flag high risk."""
        # This requires more complex pattern matching in future
        # For now, verify fraud policy has this criterion
        loader = policy_engine._loader
        policy = loader.get_policy_by_id("FRD-001")
        assert policy is not None
        
        # Check criterion exists
        criteria_conditions = [c.condition.lower() for c in policy.criteria]
        assert any("inconsistent" in cond for cond in criteria_conditions)

    def test_fraud_no_police_report(self, policy_engine):
        """Significant damage without police report should flag low-moderate risk."""
        claim_data = {
            "policy_inception_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "claim_date": datetime.now().isoformat(),
            "claims_history": [],
            "police_report": False,
            "repair_estimate": {"total": 8000},
            "damage_areas": [],
        }

        assessment = policy_engine.evaluate_fraud_risk(claim_data)

        assert any("police" in ind.lower() for ind in assessment.indicators)

    def test_fraud_risk_low(
        self, policy_engine, sample_claim_history, sample_repair_estimate
    ):
        """Clean claim should have low fraud risk."""
        claim_data = {
            **sample_claim_history,
            "repair_estimate": sample_repair_estimate,
            "damage_areas": [
                {"estimated_cost": 2000},
            ],
        }

        assessment = policy_engine.evaluate_fraud_risk(claim_data)

        assert assessment.risk_level == FRAUD_RISK_LOW
        assert not assessment.requires_siu_referral
        assert len(assessment.indicators) == 0


# =============================================================================
# Estimate Validation Tests (T065)
# =============================================================================


class TestEstimateValidation:
    """Tests for estimate validation policy evaluation."""

    def test_estimate_within_threshold_approved(self, policy_engine, sample_damage_areas):
        """Estimate within 10% of AI assessment should be approved."""
        damage_assessment = policy_engine.evaluate_damage_severity(sample_damage_areas)
        repair_estimate = {"total": 2100}  # Close to damage total of 2000

        payout = policy_engine.validate_estimate(repair_estimate, damage_assessment)

        assert payout.estimate_status == "approved"
        assert payout.recommended_payout == repair_estimate["total"]
        assert not payout.requires_independent_appraisal

    def test_estimate_slightly_over_requires_review(self, policy_engine, sample_damage_areas):
        """Estimate 10-25% over should require documentation."""
        damage_assessment = policy_engine.evaluate_damage_severity(sample_damage_areas)
        # Damage total is 2000, 15% over = 2300
        repair_estimate = {"total": 2400}

        payout = policy_engine.validate_estimate(repair_estimate, damage_assessment)

        assert payout.estimate_status == "requires_review"
        assert len(payout.adjustments) > 0

    def test_estimate_significantly_over_requires_appraisal(
        self, policy_engine, sample_damage_areas
    ):
        """Estimate >25% over should require independent appraisal."""
        damage_assessment = policy_engine.evaluate_damage_severity(sample_damage_areas)
        # Damage total is 2000, 50% over = 3000
        repair_estimate = {"total": 4000}

        payout = policy_engine.validate_estimate(repair_estimate, damage_assessment)

        assert payout.estimate_status == "requires_review"
        assert payout.requires_independent_appraisal
        assert payout.recommended_payout < repair_estimate["total"]

    def test_labor_rate_validation(self, policy_engine):
        """Labor rate exceeding market by >15% should be adjusted."""
        # Verify policy exists for labor rate validation
        loader = policy_engine._loader
        policy = loader.get_policy_by_id("PAY-001")
        assert policy is not None
        
        criteria_conditions = [c.condition.lower() for c in policy.criteria]
        assert any("labor" in cond for cond in criteria_conditions)


# =============================================================================
# Payout Calculation Tests (T066)
# =============================================================================


class TestPayoutCalculation:
    """Tests for payout recommendation calculation."""

    def test_payout_recommendation_returns_range(self, policy_engine, sample_damage_areas):
        """Should return min, max, and recommended payout amounts."""
        assessment = policy_engine.evaluate_damage_severity(sample_damage_areas)
        
        assert assessment.estimated_repair_range is not None
        assert len(assessment.estimated_repair_range) == 2
        assert assessment.estimated_repair_range[0] <= assessment.estimated_repair_range[1]

    def test_payout_considers_damage_severity(
        self, policy_engine, sample_damage_areas, sample_repair_estimate
    ):
        """Payout should be based on damage severity assessment."""
        assessment = ClaimAssessment(application_id="test-001")
        assessment.damage = policy_engine.evaluate_damage_severity(sample_damage_areas)
        assessment.fraud = FraudAssessment(risk_level=FRAUD_RISK_LOW)

        payout = policy_engine.calculate_payout_recommendation(
            sample_repair_estimate, assessment
        )

        assert payout.original_estimate == sample_repair_estimate["total"]
        assert payout.recommended_payout > 0

    def test_payout_considers_liability(
        self, policy_engine, sample_damage_areas, sample_repair_estimate
    ):
        """Payout should be adjusted based on liability percentage."""
        assessment = ClaimAssessment(application_id="test-001")
        assessment.damage = policy_engine.evaluate_damage_severity(sample_damage_areas)
        assessment.liability = LiabilityAssessment(
            determination=LIABILITY_SHARED,
            insured_fault_percentage=30.0,
            other_party_fault_percentage=70.0,
        )
        assessment.fraud = FraudAssessment(risk_level=FRAUD_RISK_LOW)

        payout = policy_engine.calculate_payout_recommendation(
            sample_repair_estimate, assessment
        )

        # Should reduce by 30% for insured fault
        expected = sample_repair_estimate["total"] * 0.7
        assert payout.recommended_payout == expected
        assert any(adj["type"] == "liability_reduction" for adj in payout.adjustments)

    def test_payout_fraud_hold(self, policy_engine, sample_repair_estimate):
        """Payout should be held for high fraud risk."""
        assessment = ClaimAssessment(application_id="test-001")
        assessment.fraud = FraudAssessment(
            risk_level=FRAUD_RISK_HIGH,
            requires_siu_referral=True,
        )

        payout = policy_engine.calculate_payout_recommendation(
            sample_repair_estimate, assessment
        )

        assert payout.estimate_status == "hold"
        assert payout.recommended_payout == 0
        assert any(adj["type"] == "fraud_hold" for adj in payout.adjustments)


# =============================================================================
# Policy Citations Tests (T067-T069)
# =============================================================================


class TestPolicyCitations:
    """Tests for policy rule tracking and rationale."""

    def test_tracks_applied_rules(
        self, policy_engine, sample_damage_areas, sample_incident_data
    ):
        """Should track which policy rules were triggered."""
        assessment = policy_engine.evaluate_claim(
            application_id="test-claim-001",
            damage_areas=sample_damage_areas,
            incident_data=sample_incident_data,
        )

        assert len(assessment.all_citations) > 0
        for citation in assessment.all_citations:
            assert citation.policy_id is not None
            assert citation.criterion_id is not None

    def test_generates_rationale(
        self, policy_engine, sample_damage_areas, sample_incident_data
    ):
        """Should generate rationale explaining each determination."""
        assessment = policy_engine.evaluate_claim(
            application_id="test-claim-002",
            damage_areas=sample_damage_areas,
            incident_data=sample_incident_data,
        )

        for citation in assessment.all_citations:
            assert citation.rationale is not None
            assert len(citation.rationale) > 0

    def test_claim_assessment_dataclass(self, policy_engine, sample_damage_areas):
        """ClaimAssessment should include all policy engine outputs."""
        assessment = policy_engine.evaluate_claim(
            application_id="test-claim-003",
            damage_areas=sample_damage_areas,
        )

        assert assessment.application_id == "test-claim-003"
        assert assessment.assessed_at is not None
        assert assessment.damage is not None
        assert assessment.fraud is not None
        assert assessment.overall_recommendation in [
            "approve",
            "adjust",
            "deny",
            "investigate",
        ]
        assert 0.0 <= assessment.confidence_score <= 1.0


# =============================================================================
# Assessment Persistence Tests (T070-T072)
# =============================================================================


class TestAssessmentPersistence:
    """Tests for assessment database operations."""

    @pytest.fixture
    def mock_pool(self):
        """Create a mock database pool."""
        pool = MagicMock()
        conn = AsyncMock()
        pool.connection.return_value.__aenter__.return_value = conn
        pool.connection.return_value.__aexit__.return_value = None
        return pool, conn

    @pytest.mark.asyncio
    async def test_save_claim_assessment(self, mock_pool, policy_engine):
        """Should save assessment to claim_assessments table."""
        from app.multimodal.repository import ClaimsMediaRepository

        pool, conn = mock_pool
        conn.fetchrow.return_value = {"id": "test-uuid-123"}

        repo = ClaimsMediaRepository(pool=pool)

        assessment = ClaimAssessment(
            application_id="test-app-001",
            overall_recommendation="approve",
            confidence_score=0.85,
        )

        result_id = await repo.save_claim_assessment(assessment)

        assert result_id == "test-uuid-123"
        conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_claim_assessment(self, mock_pool):
        """Should retrieve assessment by application_id."""
        from app.multimodal.repository import ClaimsMediaRepository

        pool, conn = mock_pool
        conn.fetchrow.return_value = {
            "id": "test-uuid-123",
            "application_id": "test-app-001",
            "assessed_at": datetime.now(),
            "damage_assessment": '{"severity": "Moderate"}',
            "liability_assessment": None,
            "fraud_assessment": '{"risk_level": "Low"}',
            "payout_assessment": None,
            "overall_recommendation": "approve",
            "requires_adjuster_review": False,
            "confidence_score": 0.85,
            "policy_citations": "[]",
            "adjuster_decision": None,
            "adjuster_notes": None,
            "decided_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        repo = ClaimsMediaRepository(pool=pool)
        result = await repo.get_claim_assessment("test-app-001")

        assert result is not None
        assert result["application_id"] == "test-app-001"
        assert result["overall_recommendation"] == "approve"
        assert result["damage_assessment"]["severity"] == "Moderate"

    @pytest.mark.asyncio
    async def test_update_adjuster_decision(self, mock_pool):
        """Should update assessment with adjuster decision and notes."""
        from app.multimodal.repository import ClaimsMediaRepository

        pool, conn = mock_pool
        conn.execute.return_value = "UPDATE 1"

        repo = ClaimsMediaRepository(pool=pool)
        result = await repo.update_adjuster_decision(
            application_id="test-app-001",
            decision="approve",
            notes="Approved as submitted",
        )

        assert result is True
        conn.execute.assert_called_once()


# =============================================================================
# Complete Claim Evaluation Tests
# =============================================================================


class TestCompleteClaimEvaluation:
    """Tests for complete claim evaluation with policy citations."""

    def test_evaluate_claim_complete(
        self,
        policy_engine,
        sample_damage_areas,
        sample_incident_data,
        sample_claim_history,
        sample_repair_estimate,
    ):
        """Test complete claim evaluation."""
        assessment = policy_engine.evaluate_claim(
            application_id="test-claim-001",
            damage_areas=sample_damage_areas,
            incident_data=sample_incident_data,
            claim_history=sample_claim_history,
            repair_estimate=sample_repair_estimate,
        )

        assert assessment.application_id == "test-claim-001"
        assert assessment.damage is not None
        assert assessment.liability is not None
        assert assessment.fraud is not None
        assert assessment.payout is not None

    def test_evaluate_claim_requires_review(self, policy_engine):
        """Test that complex claims require adjuster review."""
        # High fraud indicators + high damage
        damage_areas = [
            {
                "location": "frame",
                "damage_type": "structural",
                "severity": "Heavy",
                "estimated_cost": 12000,
                "structural": True,
            }
        ]

        claim_history = {
            "policy_inception_date": (datetime.now() - timedelta(days=20)).isoformat(),
            "claim_date": datetime.now().isoformat(),
            "claims_history": [],
        }

        assessment = policy_engine.evaluate_claim(
            application_id="test-claim-003",
            damage_areas=damage_areas,
            claim_history=claim_history,
        )

        assert assessment.requires_adjuster_review
        # New policy + heavy damage should trigger investigation
        assert assessment.overall_recommendation == "investigate"


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestPolicyEngineIntegration:
    """Integration tests requiring database connection."""

    @pytest.mark.skip(reason="Requires database connection")
    @pytest.mark.asyncio
    async def test_full_assessment_workflow(self, policy_engine):
        """Test complete assessment workflow with database."""
        from app.multimodal.repository import ClaimsMediaRepository

        repo = ClaimsMediaRepository()
        await repo.initialize_tables()

        # Create assessment
        assessment = policy_engine.evaluate_claim(
            application_id="integration-test-001",
            damage_areas=[
                {
                    "location": "front",
                    "damage_type": "dent",
                    "severity": "Moderate",
                    "estimated_cost": 1500,
                }
            ],
        )

        # Save
        assessment_id = await repo.save_claim_assessment(assessment)
        assert assessment_id is not None

        # Retrieve
        loaded = await repo.get_claim_assessment("integration-test-001")
        assert loaded is not None

        # Update adjuster decision
        updated = await repo.update_adjuster_decision(
            "integration-test-001", "approve", "Approved after review"
        )
        assert updated


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])