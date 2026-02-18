"""
OSFI B-20 Mortgage Stress Test Module.

Implements the Minimum Qualifying Rate (MQR) stress test requirements
for Canadian mortgage qualification.

Key Rules:
- MQR floor: 5.25%
- MQR calculation: Greater of (contract rate + buffer) OR floor_rate
- Applies to all federally regulated lender mortgages
- Both insured and uninsured mortgages must qualify at MQR
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from .calculator import MortgageCalculator


# Default OSFI B-20 Constants
DEFAULT_MQR_FLOOR: float = 5.25  # Minimum Qualifying Rate floor (%)
DEFAULT_MQR_BUFFER: float = 2.0   # Buffer added to contract rate (%)
MAX_GDS_INSURED: float = 0.39  # Maximum GDS for insured mortgages (as ratio)
MAX_TDS_INSURED: float = 0.44  # Maximum TDS for insured mortgages (as ratio)
MAX_GDS_UNINSURED: float = 0.39  # Maximum GDS for uninsured (B-20)
MAX_TDS_UNINSURED: float = 0.44  # Maximum TDS for uninsured (B-20)


# Insurance type mapping
INSURED_MORTGAGE_TYPES = {"high_ratio", "cmhc_insured", "genworth_insured", "canada_guaranty"}
CONVENTIONAL_MORTGAGE_TYPES = {"conventional", "uninsured"}


@dataclass
class StressTestResult:
    """Result of OSFI B-20 stress test."""
    
    passed: bool
    mqr_rate: float
    contract_rate: float
    stressed_gds: float
    stressed_tds: float
    max_gds: float
    max_tds: float
    stressed_payment: float
    contract_payment: float
    is_insured: bool
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class OSFIStressTest:
    """
    OSFI B-20 Stress Test Calculator.
    
    Implements the Minimum Qualifying Rate (MQR) stress test
    to ensure borrowers can handle higher interest rates.
    """
    
    def __init__(self, calculator: Optional[MortgageCalculator] = None):
        """
        Initialize stress test calculator.
        
        Args:
            calculator: Optional MortgageCalculator instance
        """
        self.calculator = calculator or MortgageCalculator()
    
    def apply_mqr(
        self,
        contract_rate: float,
        floor_rate: float = DEFAULT_MQR_FLOOR,
        buffer: float = DEFAULT_MQR_BUFFER
    ) -> float:
        """
        Calculate the Minimum Qualifying Rate.
        
        MQR = max(contract_rate + buffer, floor_rate)
        
        Args:
            contract_rate: The contract/offered interest rate (%)
            floor_rate: The MQR floor rate (default 5.25%)
            buffer: The buffer to add to contract rate (default 2.0%)
            
        Returns:
            The MQR to use for stress testing
        """
        buffered_rate = contract_rate + buffer
        return max(buffered_rate, floor_rate)
    
    def is_insured_mortgage(self, mortgage_type: str) -> bool:
        """
        Determine if mortgage requires default insurance.
        
        Args:
            mortgage_type: Type string (e.g., "conventional", "high_ratio", "cmhc_insured")
            
        Returns:
            True if mortgage requires insurance
        """
        mortgage_type_lower = mortgage_type.lower()
        return mortgage_type_lower in INSURED_MORTGAGE_TYPES
    
    def compute_stress_gds(
        self,
        case_data: Dict[str, Any],
        qualifying_rate: float
    ) -> float:
        """
        Compute GDS using the stress test rate.
        
        Args:
            case_data: Case data with loan, property, and income info
            qualifying_rate: The qualifying rate to use (e.g., MQR)
            
        Returns:
            GDS ratio as decimal (e.g., 0.30 for 30%)
        """
        loan = case_data.get("loan", {})
        prop = case_data.get("property", {})
        income = case_data.get("income", {})
        
        # Calculate payment at qualifying rate
        stressed_payment = self.calculator.compute_mortgage_payment(
            principal=loan.get("amount", 0),
            annual_rate=qualifying_rate,
            amortization_years=loan.get("amortizationYears", 25)
        )
        
        # Get property costs
        taxes = prop.get("taxes_monthly", 0)
        heating = prop.get("heating_monthly", 0)
        condo_fees = prop.get("condo_fees_monthly", 0)
        
        # Calculate housing costs
        piti = stressed_payment + taxes
        housing_costs = self.calculator.compute_housing_costs(
            piti=piti,
            condo_fees=condo_fees,
            heating=heating
        )
        
        # Get monthly income
        monthly_income = income.get("monthly", 0)
        
        return self.calculator.compute_gds(housing_costs, monthly_income)
    
    def compute_stress_tds(
        self,
        case_data: Dict[str, Any],
        qualifying_rate: float
    ) -> float:
        """
        Compute TDS using the stress test rate.
        
        Args:
            case_data: Case data with loan, property, income, and liabilities info
            qualifying_rate: The qualifying rate to use (e.g., MQR)
            
        Returns:
            TDS ratio as decimal (e.g., 0.34 for 34%)
        """
        loan = case_data.get("loan", {})
        prop = case_data.get("property", {})
        income = case_data.get("income", {})
        liabilities = case_data.get("liabilities", {})
        
        # Calculate payment at qualifying rate
        stressed_payment = self.calculator.compute_mortgage_payment(
            principal=loan.get("amount", 0),
            annual_rate=qualifying_rate,
            amortization_years=loan.get("amortizationYears", 25)
        )
        
        # Get property costs
        taxes = prop.get("taxes_monthly", 0)
        heating = prop.get("heating_monthly", 0)
        condo_fees = prop.get("condo_fees_monthly", 0)
        
        # Calculate housing costs
        piti = stressed_payment + taxes
        housing_costs = self.calculator.compute_housing_costs(
            piti=piti,
            condo_fees=condo_fees,
            heating=heating
        )
        
        # Get other debts and monthly income
        other_debts = liabilities.get("other_debts_monthly", 0)
        monthly_income = income.get("monthly", 0)
        
        return self.calculator.compute_tds(housing_costs, other_debts, monthly_income)
    
    def run_full_stress_test(
        self,
        case_data: Dict[str, Any],
        contract_rate: float,
        mortgage_type: str = "conventional"
    ) -> StressTestResult:
        """
        Run complete OSFI B-20 stress test.
        
        Args:
            case_data: Full case data with loan, property, income, liabilities
            contract_rate: Contract interest rate (%)
            mortgage_type: Type of mortgage (conventional, high_ratio, etc.)
            
        Returns:
            StressTestResult with pass/fail and all calculations
        """
        warnings = []
        
        # Determine if insured mortgage
        is_insured = self.is_insured_mortgage(mortgage_type)
        
        # Set ratio limits based on insurance status
        max_gds = MAX_GDS_INSURED if is_insured else MAX_GDS_UNINSURED
        max_tds = MAX_TDS_INSURED if is_insured else MAX_TDS_UNINSURED
        
        # Calculate MQR
        mqr = self.apply_mqr(contract_rate)
        
        loan = case_data.get("loan", {})
        income = case_data.get("income", {})
        
        # Calculate contract payment
        contract_payment = self.calculator.compute_mortgage_payment(
            principal=loan.get("amount", 0),
            annual_rate=contract_rate,
            amortization_years=loan.get("amortizationYears", 25)
        )
        
        # Calculate stressed payment
        stressed_payment = self.calculator.compute_mortgage_payment(
            principal=loan.get("amount", 0),
            annual_rate=mqr,
            amortization_years=loan.get("amortizationYears", 25)
        )
        
        # Calculate stressed GDS and TDS
        stressed_gds = self.compute_stress_gds(case_data, mqr)
        stressed_tds = self.compute_stress_tds(case_data, mqr)
        
        # Determine pass/fail
        gds_pass = stressed_gds <= max_gds
        tds_pass = stressed_tds <= max_tds
        passed = gds_pass and tds_pass
        
        # Build warnings
        if not gds_pass:
            warnings.append(
                f"FAIL: Stressed GDS {stressed_gds:.4f} exceeds max {max_gds}"
            )
        else:
            warnings.append(
                f"PASS: Stressed GDS {stressed_gds:.4f} within max {max_gds}"
            )
        
        if not tds_pass:
            warnings.append(
                f"FAIL: Stressed TDS {stressed_tds:.4f} exceeds max {max_tds}"
            )
        else:
            warnings.append(
                f"PASS: Stressed TDS {stressed_tds:.4f} within max {max_tds}"
            )
        
        if is_insured:
            warnings.append("High-ratio mortgage requires default insurance")
        
        if contract_payment > 0:
            payment_increase = stressed_payment - contract_payment
            payment_increase_pct = (payment_increase / contract_payment) * 100
            warnings.append(
                f"Stress test increases payment by ${payment_increase:,.2f} "
                f"({payment_increase_pct:.1f}%)"
            )
        
        return StressTestResult(
            passed=passed,
            mqr_rate=mqr,
            contract_rate=contract_rate,
            stressed_gds=stressed_gds,
            stressed_tds=stressed_tds,
            max_gds=max_gds,
            max_tds=max_tds,
            stressed_payment=stressed_payment,
            contract_payment=contract_payment,
            is_insured=is_insured,
            warnings=warnings,
            details={
                "loan": loan,
                "monthly_income": income.get("monthly", 0),
            }
        )
    
    def calculate_max_mortgage(
        self,
        monthly_income: float,
        contract_rate: float,
        amortization_years: int,
        monthly_property_tax: float,
        monthly_heating: float = 100.0,
        monthly_condo_fees: float = 0.0,
        other_monthly_debts: float = 0.0,
        target_gds: float = 0.32,
        target_tds: float = 0.40
    ) -> Dict[str, Any]:
        """
        Calculate maximum mortgage amount based on income and target ratios.
        
        Uses the MQR stress rate to determine maximum qualification.
        
        Args:
            monthly_income: Gross monthly income
            contract_rate: Expected contract rate (%)
            amortization_years: Amortization period
            monthly_property_tax: Estimated monthly property tax
            monthly_heating: Monthly heating costs
            monthly_condo_fees: Monthly condo fees
            other_monthly_debts: Other monthly debt payments
            target_gds: Target GDS ratio (default 0.32)
            target_tds: Target TDS ratio (default 0.40)
            
        Returns:
            Dictionary with maximum mortgage details
        """
        # Calculate MQR
        mqr = self.apply_mqr(contract_rate)
        
        # Calculate maximum housing payment based on GDS
        condo_portion = monthly_condo_fees * 0.5
        fixed_housing_costs = monthly_property_tax + monthly_heating + condo_portion
        max_housing_payment_gds = (monthly_income * target_gds) - fixed_housing_costs
        
        # Calculate maximum total debt payment based on TDS
        max_total_payment_tds = monthly_income * target_tds
        max_housing_payment_tds = max_total_payment_tds - other_monthly_debts - fixed_housing_costs
        
        # Take the lower of the two
        max_mortgage_payment = min(max_housing_payment_gds, max_housing_payment_tds)
        
        if max_mortgage_payment <= 0:
            return {
                "max_mortgage": 0,
                "limiting_factor": "income_insufficient",
                "max_payment": 0,
                "mqr_rate": mqr,
                "target_gds": target_gds,
                "target_tds": target_tds
            }
        
        # Reverse calculate principal from payment
        # Using semi-annual compounding
        semi_annual_rate = mqr / 100.0 / 2.0
        monthly_rate = (1 + semi_annual_rate) ** (1/6) - 1
        total_payments = amortization_years * 12
        
        # P = Payment * [(1+r)^n - 1] / [r * (1+r)^n]
        if monthly_rate > 0:
            factor = ((1 + monthly_rate) ** total_payments - 1) / (
                monthly_rate * (1 + monthly_rate) ** total_payments
            )
            max_mortgage = max_mortgage_payment * factor
        else:
            max_mortgage = max_mortgage_payment * total_payments
        
        limiting_factor = "gds" if max_housing_payment_gds <= max_housing_payment_tds else "tds"
        
        return {
            "max_mortgage": round(max_mortgage, 2),
            "limiting_factor": limiting_factor,
            "max_payment": round(max_mortgage_payment, 2),
            "mqr_rate": mqr,
            "contract_rate": contract_rate,
            "target_gds": target_gds,
            "target_tds": target_tds,
            "monthly_income": monthly_income,
            "max_gds_payment": round(max_housing_payment_gds, 2),
            "max_tds_payment": round(max_housing_payment_tds, 2)
        }
