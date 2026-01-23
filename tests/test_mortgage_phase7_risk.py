"""
Tests for Phase 7: Risk Analysis Service
Feature: 008-mortgage-underwriting

Tests cover:
- Income consistency checks
- Fraud detection signals
- AML triage and risk scoring
- Credit risk analysis
- Risk signal aggregation
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal


class TestIncomeConsistencyEngine:
    """Tests for income consistency checks across documents."""

    @pytest.fixture
    def consistency_engine(self):
        """Return an IncomeConsistencyEngine instance."""
        from app.mortgage.risk_analysis import IncomeConsistencyEngine
        return IncomeConsistencyEngine()

    @pytest.fixture
    def consistent_income_data(self):
        """Return consistent income data from multiple documents."""
        return {
            "application": {"stated_annual_income": 120000},
            "paystub": {"ytd_gross": 60000, "pay_date": "2024-06-15"},
            "employment_letter": {"annual_salary": 120000},
            "t4": {"year": 2023, "income": 118000},
        }

    @pytest.fixture
    def inconsistent_income_data(self):
        """Return inconsistent income data (mismatch)."""
        return {
            "application": {"stated_annual_income": 150000},
            "paystub": {"ytd_gross": 50000, "pay_date": "2024-06-15"},
            "employment_letter": {"annual_salary": 100000},
            "t4": {"year": 2023, "income": 95000},
        }

    def test_detect_consistent_income(self, consistency_engine, consistent_income_data):
        """Should detect consistent income across documents."""
        result = consistency_engine.check_consistency(consistent_income_data)
        
        assert result.is_consistent is True
        assert len(result.discrepancies) == 0

    def test_detect_income_discrepancy(self, consistency_engine, inconsistent_income_data):
        """Should detect income discrepancies across documents."""
        result = consistency_engine.check_consistency(inconsistent_income_data)
        
        assert result.is_consistent is False
        assert len(result.discrepancies) > 0

    def test_calculate_variance_percentage(self, consistency_engine):
        """Should calculate variance between stated and verified income."""
        stated = 120000
        verified = 100000
        
        variance = consistency_engine.calculate_variance(stated, verified)
        
        # (120000 - 100000) / 100000 = 20%
        assert variance == 0.20

    def test_flag_high_variance(self, consistency_engine, inconsistent_income_data):
        """Should flag variance exceeding threshold."""
        result = consistency_engine.check_consistency(
            inconsistent_income_data,
            variance_threshold=0.10  # 10%
        )
        
        assert result.is_consistent is False
        assert any(d.severity == "high" for d in result.discrepancies)

    def test_ytd_to_annual_projection(self, consistency_engine):
        """Should project YTD income to annual correctly."""
        ytd_gross = 60000
        pay_date = "2024-06-15"  # Mid-year
        
        projected_annual = consistency_engine.project_annual_income(ytd_gross, pay_date)
        
        # 60000 / 0.458 (roughly 167 days / 365) ≈ 120,000
        assert 115000 < projected_annual < 135000


class TestFraudDetectionEngine:
    """Tests for fraud signal detection."""

    @pytest.fixture
    def fraud_engine(self):
        """Return a FraudDetectionEngine instance."""
        from app.mortgage.risk_analysis import FraudDetectionEngine
        return FraudDetectionEngine()

    def test_detect_round_number_income(self, fraud_engine):
        """Should flag suspiciously round income figures."""
        income_data = {"annual_income": 100000}  # Perfectly round
        
        signals = fraud_engine.analyze_income(income_data)
        
        # May or may not flag depending on threshold
        round_signal = next((s for s in signals if "round" in s.description.lower()), None)
        # This is informational, not necessarily fraud

    def test_detect_employment_length_mismatch(self, fraud_engine):
        """Should detect employment length inconsistencies."""
        data = {
            "application": {"employer_start_date": "2020-01-15"},
            "employment_letter": {"tenure": "5 years"},
            "current_date": "2024-06-15",
        }
        
        signals = fraud_engine.check_employment_consistency(data)
        
        # 4.5 years vs "5 years" - minor discrepancy
        assert all(s.severity != "high" for s in signals)

    def test_detect_significant_employment_discrepancy(self, fraud_engine):
        """Should flag significant employment discrepancies."""
        data = {
            "application": {"employer_start_date": "2023-06-15"},
            "employment_letter": {"tenure": "5 years"},
            "current_date": "2024-06-15",
        }
        
        signals = fraud_engine.check_employment_consistency(data)
        
        # 1 year vs "5 years" - significant discrepancy
        assert any(s.severity == "high" for s in signals)

    def test_detect_property_flip_risk(self, fraud_engine):
        """Should detect potential property flipping."""
        data = {
            "property": {
                "last_sale_date": "2024-01-01",
                "last_sale_price": 500000,
                "current_purchase_price": 650000,
                "appraisal_date": "2024-06-01",
            }
        }
        
        signals = fraud_engine.check_property_flip(data)
        
        # 30% increase in 5 months is suspicious
        assert len(signals) > 0

    def test_detect_straw_buyer_signals(self, fraud_engine):
        """Should detect straw buyer risk signals."""
        data = {
            "borrower": {
                "income": 50000,
                "down_payment_source": "gift",
                "gift_amount": 170000,
            },
            "property": {
                "price": 850000,
                "occupancy": "owner_occupied",
            }
        }
        
        signals = fraud_engine.check_straw_buyer_risk(data)
        
        # Large gift relative to income may be a signal
        # Not necessarily fraud, but should be flagged for review


class TestAMLTriageEngine:
    """Tests for AML (Anti-Money Laundering) triage."""

    @pytest.fixture
    def aml_engine(self):
        """Return an AMLTriageEngine instance."""
        from app.mortgage.risk_analysis import AMLTriageEngine
        return AMLTriageEngine()

    def test_check_down_payment_source(self, aml_engine):
        """Should verify down payment source documentation."""
        data = {
            "down_payment": 170000,
            "source": "savings",
            "bank_statements_months": 3,
            "accumulation_pattern": "gradual",
        }
        
        result = aml_engine.check_down_payment_source(data)
        
        assert result.risk_level in ["low", "medium", "high"]

    def test_flag_large_cash_deposits(self, aml_engine):
        """Should flag large recent cash deposits."""
        data = {
            "bank_statement_transactions": [
                {"type": "deposit", "amount": 15000, "description": "CASH DEP"},
                {"type": "deposit", "amount": 12000, "description": "CASH DEP"},
            ]
        }
        
        signals = aml_engine.analyze_deposits(data)
        
        # Large cash deposits should be flagged
        assert any("cash" in s.description.lower() for s in signals)

    def test_flag_structured_deposits(self, aml_engine):
        """Should detect potential structuring (multiple deposits just under threshold)."""
        data = {
            "bank_statement_transactions": [
                {"type": "deposit", "amount": 9500, "date": "2024-06-01"},
                {"type": "deposit", "amount": 9500, "date": "2024-06-03"},
                {"type": "deposit", "amount": 9500, "date": "2024-06-05"},
            ]
        }
        
        signals = aml_engine.detect_structuring(data)
        
        # Multiple deposits just under $10K threshold
        assert len(signals) > 0

    def test_check_gift_letter_compliance(self, aml_engine):
        """Should verify gift letter requirements."""
        data = {
            "gift_amount": 50000,
            "donor_relationship": "parent",
            "donor_account_verified": True,
            "repayment_required": False,
        }
        
        result = aml_engine.check_gift_compliance(data)
        
        assert result.compliant is True

    def test_flag_non_arms_length_transaction(self, aml_engine):
        """Should flag non-arm's length transactions."""
        data = {
            "seller_relationship": "family_member",
            "purchase_price": 650000,
            "appraisal_value": 750000,
        }
        
        signals = aml_engine.check_arms_length(data)
        
        # Below-market purchase from family should be flagged
        assert len(signals) > 0


class TestCreditRiskAnalysis:
    """Tests for credit risk analysis."""

    @pytest.fixture
    def credit_engine(self):
        """Return a CreditRiskEngine instance."""
        from app.mortgage.risk_analysis import CreditRiskEngine
        return CreditRiskEngine()

    def test_categorize_credit_score_excellent(self, credit_engine):
        """Should categorize credit scores correctly."""
        result = credit_engine.categorize_score(780)
        
        assert result == "excellent"

    def test_categorize_credit_score_fair(self, credit_engine):
        """Should categorize fair credit score."""
        result = credit_engine.categorize_score(650)
        
        assert result == "fair"

    def test_detect_thin_credit_file(self, credit_engine):
        """Should detect thin credit file."""
        data = {
            "credit_score": 680,
            "trade_lines": 2,
            "oldest_trade_months": 12,
        }
        
        result = credit_engine.analyze_credit_depth(data)
        
        assert result.thin_file is True

    def test_detect_recent_derogatory(self, credit_engine):
        """Should detect recent derogatory items."""
        data = {
            "credit_score": 680,
            "derogatory_items": [
                {"type": "late_payment", "months_ago": 6},
            ]
        }
        
        signals = credit_engine.check_derogatory_items(data)
        
        assert len(signals) > 0

    def test_check_debt_utilization(self, credit_engine):
        """Should check credit card utilization."""
        data = {
            "credit_cards": [
                {"limit": 10000, "balance": 8000},  # 80% utilized
                {"limit": 5000, "balance": 2500},   # 50% utilized
            ]
        }
        
        result = credit_engine.check_utilization(data)
        
        # High utilization on one card
        assert result.has_high_utilization is True


class TestRiskSignalAggregation:
    """Tests for risk signal aggregation."""

    @pytest.fixture
    def aggregator(self):
        """Return a RiskSignalAggregator instance."""
        from app.mortgage.risk_analysis import RiskSignalAggregator
        return RiskSignalAggregator()

    def test_aggregate_signals_from_engines(self, aggregator):
        """Should aggregate signals from all risk engines."""
        income_signals = [MagicMock(category="income", severity="medium")]
        fraud_signals = [MagicMock(category="fraud", severity="low")]
        aml_signals = []
        credit_signals = [MagicMock(category="credit", severity="low")]
        
        result = aggregator.aggregate(income_signals, fraud_signals, aml_signals, credit_signals)
        
        assert result.total_signals == 3

    def test_compute_overall_risk_score(self, aggregator):
        """Should compute overall risk score."""
        signals = [
            MagicMock(severity="low", weight=1),
            MagicMock(severity="medium", weight=2),
            MagicMock(severity="high", weight=5),
        ]
        
        score = aggregator.compute_risk_score(signals)
        
        # Score should reflect weighted sum
        assert 0 <= score <= 100

    def test_categorize_risk_level(self, aggregator):
        """Should categorize overall risk level."""
        low_score = 15
        medium_score = 45
        high_score = 75
        
        assert aggregator.categorize_risk(low_score) == "low"
        assert aggregator.categorize_risk(medium_score) == "medium"
        assert aggregator.categorize_risk(high_score) == "high"

    def test_generate_risk_summary(self, aggregator):
        """Should generate human-readable risk summary."""
        signals = [
            MagicMock(category="income", description="Income variance 15%"),
            MagicMock(category="fraud", description="Recent property flip"),
        ]
        
        summary = aggregator.generate_summary(signals)
        
        assert "income" in summary.lower()
        assert len(summary) > 50


class TestRiskAnalysisProvenance:
    """Tests for risk analysis provenance tracking."""

    def test_risk_signal_has_source(self):
        """Risk signal should include source document."""
        from app.mortgage.risk_analysis import RiskSignal
        
        signal = RiskSignal(
            category="income",
            severity="medium",
            description="Income variance detected",
            source_documents=["paystub_001", "employment_letter_001"],
            evidence={"stated": 120000, "verified": 100000},
        )
        
        assert len(signal.source_documents) == 2

    def test_risk_signal_has_evidence(self):
        """Risk signal should include evidence data."""
        from app.mortgage.risk_analysis import RiskSignal
        
        signal = RiskSignal(
            category="fraud",
            severity="high",
            description="Property flip detected",
            source_documents=["title_search_001"],
            evidence={"months_since_last_sale": 4, "price_increase_pct": 0.30},
        )
        
        assert signal.evidence["price_increase_pct"] == 0.30

    def test_risk_report_traceable(self):
        """Risk report should be traceable to source signals."""
        from app.mortgage.risk_analysis import RiskReport
        
        report = RiskReport(
            overall_score=45,
            risk_level="medium",
            signals=[
                {"id": "sig_001", "category": "income"},
                {"id": "sig_002", "category": "credit"},
            ],
            recommendations=["Verify employment", "Request additional bank statements"],
        )
        
        assert len(report.signals) == 2
        assert len(report.recommendations) > 0
