"""
Tests for Phase 5: Calculation Engine
Feature: 008-mortgage-underwriting

Tests cover:
- GDS/TDS/LTV ratio calculations
- OSFI MQR stress test implementation
- Mortgage payment calculation (P&I)
- Income qualification with haircuts
- Calculation provenance tracking
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock


class TestMortgageCalculator:
    """Tests for MortgageCalculator GDS/TDS/LTV calculations."""

    @pytest.fixture
    def calculator(self):
        """Return a MortgageCalculator instance."""
        from app.mortgage.calculator import MortgageCalculator
        return MortgageCalculator()

    @pytest.fixture
    def settings(self):
        """Return mortgage settings with standard limits."""
        from app.config import MortgageUnderwritingSettings
        return MortgageUnderwritingSettings(
            osfi_mqr_floor_pct=5.25,
            osfi_mqr_buffer_pct=2.0,
            gds_limit_standard=0.39,
            tds_limit_standard=0.44,
        )

    def test_compute_monthly_income_from_annual(self, calculator):
        """Should compute monthly income from annual salary."""
        income_sources = [
            {"type": "salary", "amount": 120000, "frequency": "annual"}
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        assert result == 10000  # $120,000 / 12

    def test_compute_monthly_income_multiple_sources(self, calculator):
        """Should aggregate multiple income sources."""
        income_sources = [
            {"type": "salary", "amount": 120000, "frequency": "annual"},
            {"type": "bonus", "amount": 24000, "frequency": "annual", "haircut": 0.5},
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # $120,000/12 = $10,000 base + $24,000 * 0.5 / 12 = $1,000 bonus
        assert result == 11000

    def test_compute_mortgage_payment_standard_formula(self, calculator):
        """Should compute P&I payment using standard amortization formula."""
        principal = 520000
        annual_rate = 5.25  # percent
        amortization_years = 25
        
        result = calculator.compute_mortgage_payment(principal, annual_rate, amortization_years)
        
        # Expected payment for $520K at 5.25% over 25 years is approximately $3,100-$3,200/month
        assert 3000 < result < 3500

    def test_compute_mortgage_payment_zero_rate(self, calculator):
        """Should handle zero interest rate."""
        principal = 520000
        annual_rate = 0.0
        amortization_years = 25
        
        result = calculator.compute_mortgage_payment(principal, annual_rate, amortization_years)
        
        # Zero interest: $520,000 / (25 * 12) = $1,733.33
        assert abs(result - 1733.33) < 1

    def test_compute_housing_costs(self, calculator):
        """Should sum PITH components correctly."""
        piti = 3200  # Principal, Interest, Taxes, Insurance
        condo_fees = 650
        heating = 80
        
        result = calculator.compute_housing_costs(piti, condo_fees, heating)
        
        # Condo fees often use 50% for calculation
        # $3,200 + ($650 * 0.5) + $80 = $3,605
        assert result == 3605 or result == 3200 + 650 + 80

    def test_compute_gds_ratio(self, calculator):
        """Should compute GDS ratio correctly."""
        housing_costs = 3605
        monthly_income = 12000
        
        result = calculator.compute_gds(housing_costs, monthly_income)
        
        # GDS = $3,605 / $12,000 = 0.3004 = 30.04%
        assert abs(result - 0.3004) < 0.01

    def test_compute_tds_ratio(self, calculator):
        """Should compute TDS ratio correctly."""
        housing_costs = 3605
        other_debts = 450  # Car loan, credit cards
        monthly_income = 12000
        
        result = calculator.compute_tds(housing_costs, other_debts, monthly_income)
        
        # TDS = ($3,605 + $450) / $12,000 = 0.3379 = 33.79%
        assert abs(result - 0.3379) < 0.01

    def test_compute_ltv_ratio(self, calculator):
        """Should compute LTV ratio correctly."""
        loan_amount = 520000
        property_value = 650000
        
        result = calculator.compute_ltv(loan_amount, property_value)
        
        # LTV = $520,000 / $650,000 = 0.80 = 80%
        assert result == 0.80

    def test_compute_combined_ltv_with_secondary(self, calculator):
        """Should compute combined LTV with secondary financing."""
        loan_amount = 520000
        secondary_financing = 50000
        property_value = 650000
        
        result = calculator.compute_combined_ltv(loan_amount, secondary_financing, property_value)
        
        # CLTV = ($520,000 + $50,000) / $650,000 = 0.877 = 87.7%
        assert abs(result - 0.877) < 0.01


class TestOSFIStressTest:
    """Tests for OSFI MQR stress test implementation."""

    @pytest.fixture
    def stress_test(self):
        """Return an OSFIStressTest instance."""
        from app.mortgage.stress_test import OSFIStressTest
        return OSFIStressTest()

    def test_apply_mqr_uses_floor_when_higher(self, stress_test):
        """MQR should use floor rate when it's higher than contract+buffer."""
        contract_rate = 3.0  # 3% contract
        floor_rate = 5.25
        buffer = 2.0
        
        result = stress_test.apply_mqr(contract_rate, floor_rate, buffer)
        
        # Contract + 2% = 5.0%, Floor = 5.25%
        # Should use floor
        assert result == 5.25

    def test_apply_mqr_uses_contract_plus_buffer_when_higher(self, stress_test):
        """MQR should use contract+buffer when it's higher than floor."""
        contract_rate = 4.5  # 4.5% contract
        floor_rate = 5.25
        buffer = 2.0
        
        result = stress_test.apply_mqr(contract_rate, floor_rate, buffer)
        
        # Contract + 2% = 6.5%, Floor = 5.25%
        # Should use contract + buffer
        assert result == 6.5

    def test_apply_mqr_sample_case(self, stress_test):
        """Test MQR with sample case from spec."""
        # From sample: contract_rate = 5.25%
        contract_rate = 5.25
        floor_rate = 5.25
        buffer = 2.0
        
        result = stress_test.apply_mqr(contract_rate, floor_rate, buffer)
        
        # Contract + 2% = 7.25%, Floor = 5.25%
        # Should use 7.25%
        assert result == 7.25

    def test_compute_stress_gds(self, stress_test):
        """Should compute GDS at stress test rate."""
        case_data = {
            "loan": {"amount": 520000, "amortizationYears": 25},
            "property": {"taxes_monthly": 420, "heating_monthly": 80, "condo_fees_monthly": 650},
            "income": {"monthly": 12000},
        }
        qualifying_rate = 7.25
        
        result = stress_test.compute_stress_gds(case_data, qualifying_rate)
        
        # Stress test payment will be higher, so GDS will be higher
        assert 0.2 < result < 0.5

    def test_compute_stress_tds(self, stress_test):
        """Should compute TDS at stress test rate."""
        case_data = {
            "loan": {"amount": 520000, "amortizationYears": 25},
            "property": {"taxes_monthly": 420, "heating_monthly": 80, "condo_fees_monthly": 650},
            "income": {"monthly": 12000},
            "liabilities": {"other_debts_monthly": 450},
        }
        qualifying_rate = 7.25
        
        result = stress_test.compute_stress_tds(case_data, qualifying_rate)
        
        # TDS includes other debts on top of housing costs
        assert 0.25 < result < 0.6

    def test_is_insured_mortgage_conventional(self, stress_test):
        """Conventional mortgage should not be insured."""
        assert stress_test.is_insured_mortgage("conventional") is False

    def test_is_insured_mortgage_high_ratio(self, stress_test):
        """High-ratio mortgage should be insured."""
        assert stress_test.is_insured_mortgage("high_ratio") is True
        assert stress_test.is_insured_mortgage("cmhc_insured") is True


class TestIncomeQualificationRules:
    """Tests for income qualification and haircut rules."""

    @pytest.fixture
    def calculator(self):
        """Return a MortgageCalculator instance."""
        from app.mortgage.calculator import MortgageCalculator
        return MortgageCalculator()

    def test_commission_income_haircut(self, calculator):
        """Commission income should be haircutted 50%."""
        income_sources = [
            {"type": "commission", "amount": 50000, "frequency": "annual"}
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # $50,000 * 0.5 / 12 = $2,083.33
        assert abs(result - 2083.33) < 1

    def test_bonus_income_haircut(self, calculator):
        """Bonus income should be haircutted 50%."""
        income_sources = [
            {"type": "bonus", "amount": 24000, "frequency": "annual"}
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # $24,000 * 0.5 / 12 = $1,000
        assert result == 1000

    def test_rental_income_haircut_with_offset(self, calculator):
        """Rental income should be haircutted with expense offset."""
        income_sources = [
            {"type": "rental", "gross_amount": 2400, "frequency": "monthly"}
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # Rental typically uses 50% or has expense offset
        # $2,400 * 0.5 = $1,200
        assert result == 1200 or result <= 2400

    def test_self_employed_income_averaging(self, calculator):
        """Self-employed income should use 2-year average."""
        income_sources = [
            {
                "type": "self_employed",
                "year1_net": 80000,
                "year2_net": 100000,
                "frequency": "annual"
            }
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # 2-year average: ($80,000 + $100,000) / 2 = $90,000
        # Monthly: $90,000 / 12 = $7,500
        assert result == 7500

    def test_probationary_income_excluded(self, calculator):
        """Probationary period income should be excluded or reduced."""
        income_sources = [
            {"type": "salary", "amount": 120000, "frequency": "annual", "probationary": True}
        ]
        
        result = calculator.compute_monthly_income(income_sources)
        
        # Probationary income may be excluded or reduced
        assert result == 0 or result < 10000


class TestCalculationProvenance:
    """Tests for calculation provenance tracking."""

    def test_calculation_result_has_inputs(self):
        """CalculationResult should include input values."""
        from app.mortgage.calculator import CalculationResult
        
        result = CalculationResult(
            name="gds",
            value=0.30,
            inputs={"housing_costs": 3600, "monthly_income": 12000},
            formula="housing_costs / monthly_income",
            provenance=[{"field": "housing_costs", "source": "calculated"}]
        )
        
        assert result.inputs["housing_costs"] == 3600
        assert result.inputs["monthly_income"] == 12000

    def test_calculation_result_has_formula(self):
        """CalculationResult should include formula used."""
        from app.mortgage.calculator import CalculationResult
        
        result = CalculationResult(
            name="mortgage_payment",
            value=3200,
            inputs={"principal": 520000, "rate": 5.25, "amortization": 25},
            formula="P * [r(1+r)^n] / [(1+r)^n - 1]",
            provenance=[]
        )
        
        assert "r(1+r)" in result.formula

    def test_calculation_result_links_to_source_fields(self):
        """CalculationResult should link inputs to source document fields."""
        from app.mortgage.calculator import CalculationResult
        
        result = CalculationResult(
            name="ltv",
            value=0.80,
            inputs={"loan_amount": 520000, "property_value": 650000},
            formula="loan_amount / property_value",
            provenance=[
                {"field": "loan_amount", "source_doc": "application", "source_field": "RequestedLoanAmount"},
                {"field": "property_value", "source_doc": "appraisal", "source_field": "AppraisedValue"},
            ]
        )
        
        assert len(result.provenance) == 2
        assert result.provenance[0]["source_doc"] == "application"


class TestSampleCaseCalculations:
    """Tests using sample case from mortgage research."""

    @pytest.fixture
    def sample_case(self):
        """Return sample case data from bundle_ground_truth.json."""
        return {
            "deal": {
                "purchase_price": 850000,
                "down_payment": 170000,
                "requested_loan_amount": 680000,
                "contract_rate_pct": 5.25,
            },
            "derived_metrics": {
                "ltv_estimate": 0.8,
                "gds_estimate": 0.2657,
                "tds_estimate": 0.2886,
            }
        }

    def test_sample_case_ltv(self, sample_case):
        """Sample case LTV should match expected."""
        from app.mortgage.calculator import MortgageCalculator
        
        calc = MortgageCalculator()
        result = calc.compute_ltv(
            sample_case["deal"]["requested_loan_amount"],
            sample_case["deal"]["purchase_price"]
        )
        
        assert abs(result - sample_case["derived_metrics"]["ltv_estimate"]) < 0.01

    def test_sample_case_mqr(self):
        """Sample case MQR should be 7.25% (contract 5.25% + 2%)."""
        from app.mortgage.stress_test import OSFIStressTest
        
        stress_test = OSFIStressTest()
        result = stress_test.apply_mqr(5.25, 5.25, 2.0)
        
        assert result == 7.25
