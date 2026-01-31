"""
Mortgage ratio and payment calculator module.

Implements Canadian mortgage calculations including:
- Monthly payment using amortization formula
- GDS (Gross Debt Service) ratio
- TDS (Total Debt Service) ratio
- LTV (Loan-to-Value) ratio
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
import math


@dataclass
class CalculationResult:
    """Result of a mortgage calculation with metadata."""
    
    name: str
    value: float
    inputs: Dict[str, Any]
    formula: str
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# Default haircuts for income types (50% = 0.5 factor)
DEFAULT_INCOME_HAIRCUTS = {
    "salary": 1.0,
    "base": 1.0,
    "commission": 0.5,
    "bonus": 0.5,
    "overtime": 0.5,
    "rental": 0.5,
    "self_employed": 1.0,  # Uses averaging
}

# Condo fee factor (50% counted toward housing costs)
CONDO_FEE_FACTOR = 0.5


class MortgageCalculator:
    """
    Canadian mortgage ratio calculator.
    
    Implements OSFI B-20 compliant calculations for GDS, TDS, and LTV ratios.
    """
    
    def __init__(self):
        """Initialize calculator."""
        pass
    
    def compute_monthly_income(
        self,
        income_sources: List[Dict[str, Any]]
    ) -> float:
        """
        Compute gross monthly income from income sources with haircuts.
        
        Args:
            income_sources: List of income source dicts with:
                - type: Income type (salary, bonus, commission, rental, self_employed)
                - amount: Income amount (for annual/monthly)
                - frequency: "annual" or "monthly"
                - haircut: Optional explicit haircut factor (0-1)
                - probationary: Optional bool (excludes income if True)
                - gross_amount: For rental income
                - year1_net, year2_net: For self-employed (2-year average)
                
        Returns:
            Monthly qualified income
        """
        total_monthly = 0.0
        
        for source in income_sources:
            income_type = source.get("type", "salary")
            frequency = source.get("frequency", "annual")
            is_probationary = source.get("probationary", False)
            
            # Probationary income excluded
            if is_probationary:
                continue
            
            # Get amount based on income type
            if income_type == "self_employed":
                # Use 2-year average
                year1 = source.get("year1_net", 0)
                year2 = source.get("year2_net", 0)
                annual_amount = (year1 + year2) / 2.0
                haircut = 1.0  # No additional haircut after averaging
            elif income_type == "rental":
                # Rental uses gross_amount with 50% haircut
                gross_amount = source.get("gross_amount", source.get("amount", 0))
                haircut = source.get("haircut", DEFAULT_INCOME_HAIRCUTS.get("rental", 0.5))
                if frequency == "monthly":
                    annual_amount = gross_amount * 12
                else:
                    annual_amount = gross_amount
            else:
                # Standard income
                annual_amount = source.get("amount", 0)
                if frequency == "monthly":
                    annual_amount *= 12
                
                # Apply haircut
                haircut = source.get("haircut", DEFAULT_INCOME_HAIRCUTS.get(income_type, 1.0))
            
            # Calculate monthly contribution
            monthly = (annual_amount * haircut) / 12.0
            total_monthly += monthly
        
        return round(total_monthly, 2)
    
    def compute_mortgage_payment(
        self,
        principal: float,
        annual_rate: float,
        amortization_years: int,
        payment_frequency: str = "monthly"
    ) -> float:
        """
        Compute mortgage payment using Canadian amortization formula.
        
        Uses semi-annual compounding as per Canadian mortgage standards.
        
        Args:
            principal: Loan principal amount
            annual_rate: Annual interest rate (e.g., 5.25 for 5.25%)
            amortization_years: Amortization period in years
            payment_frequency: Payment frequency (monthly, bi-weekly, weekly)
            
        Returns:
            Monthly payment amount
        """
        # Handle zero rate
        if annual_rate <= 0:
            return round(principal / (amortization_years * 12), 2)
        
        # Validate inputs
        if principal <= 0 or amortization_years <= 0:
            return 0.0
        
        # Canadian mortgages use semi-annual compounding
        semi_annual_rate = annual_rate / 100.0 / 2.0
        
        # Convert to effective monthly rate
        monthly_rate = (1 + semi_annual_rate) ** (1/6) - 1
        
        # Total number of payments
        total_payments = amortization_years * 12
        
        # Standard amortization formula: P * r * (1+r)^n / ((1+r)^n - 1)
        numerator = principal * monthly_rate * ((1 + monthly_rate) ** total_payments)
        denominator = ((1 + monthly_rate) ** total_payments) - 1
        payment = numerator / denominator
        
        return round(payment, 2)
    
    def compute_housing_costs(
        self,
        piti: float,
        condo_fees: float = 0.0,
        heating: float = 0.0
    ) -> float:
        """
        Compute total housing costs for GDS calculation.
        
        Args:
            piti: Principal, Interest, Taxes, Insurance payment
            condo_fees: Monthly condo/strata fees (50% counted)
            heating: Monthly heating costs
            
        Returns:
            Total housing costs
        """
        # Count 50% of condo fees per standard practice
        condo_portion = condo_fees * CONDO_FEE_FACTOR
        return piti + condo_portion + heating
    
    def compute_gds(
        self,
        housing_costs: float,
        monthly_income: float
    ) -> float:
        """
        Compute Gross Debt Service (GDS) ratio.
        
        GDS = Housing Costs / Gross Income
        
        Args:
            housing_costs: Total monthly housing costs
            monthly_income: Gross monthly income
            
        Returns:
            GDS ratio as decimal (e.g., 0.30 for 30%)
        """
        if monthly_income <= 0:
            return 0.0
        
        return round(housing_costs / monthly_income, 4)
    
    def compute_tds(
        self,
        housing_costs: float,
        other_debts: float,
        monthly_income: float
    ) -> float:
        """
        Compute Total Debt Service (TDS) ratio.
        
        TDS = (Housing Costs + Other Debts) / Gross Income
        
        Args:
            housing_costs: Total monthly housing costs
            other_debts: Other monthly debt payments
            monthly_income: Gross monthly income
            
        Returns:
            TDS ratio as decimal (e.g., 0.34 for 34%)
        """
        if monthly_income <= 0:
            return 0.0
        
        total_payments = housing_costs + other_debts
        return round(total_payments / monthly_income, 4)
    
    def compute_ltv(
        self,
        loan_amount: float,
        property_value: float
    ) -> float:
        """
        Compute Loan-to-Value (LTV) ratio.
        
        LTV = Loan Amount / Property Value
        
        Args:
            loan_amount: Total mortgage loan amount
            property_value: Property value
            
        Returns:
            LTV ratio as decimal (e.g., 0.80 for 80%)
        """
        if property_value <= 0:
            return 0.0
        
        return round(loan_amount / property_value, 4)
    
    def compute_combined_ltv(
        self,
        loan_amount: float,
        secondary_financing: float,
        property_value: float
    ) -> float:
        """
        Compute Combined Loan-to-Value (CLTV) ratio.
        
        CLTV = (Primary Loan + Secondary Financing) / Property Value
        
        Args:
            loan_amount: Primary mortgage loan amount
            secondary_financing: Secondary/other financing
            property_value: Property value
            
        Returns:
            CLTV ratio as decimal
        """
        if property_value <= 0:
            return 0.0
        
        combined = loan_amount + secondary_financing
        return round(combined / property_value, 4)
    
    def compute_down_payment_percent(
        self,
        down_payment: float,
        purchase_price: float
    ) -> float:
        """
        Compute down payment as percentage of purchase price.
        
        Args:
            down_payment: Down payment amount
            purchase_price: Purchase price of property
            
        Returns:
            Down payment as decimal (e.g., 0.20 for 20%)
        """
        if purchase_price <= 0:
            return 0.0
        
        return round(down_payment / purchase_price, 4)
    
    def compute_all_ratios(
        self,
        loan_amount: float,
        property_value: float,
        annual_rate: float,
        amortization_years: int,
        income_sources: List[Dict[str, Any]],
        monthly_property_tax: float,
        monthly_heating: float = 100.0,
        monthly_condo_fees: float = 0.0,
        other_monthly_debts: float = 0.0
    ) -> Dict[str, CalculationResult]:
        """
        Compute all mortgage qualification ratios at once.
        
        Returns:
            Dictionary with all calculation results
        """
        # Calculate monthly income
        monthly_income = self.compute_monthly_income(income_sources)
        
        # Calculate mortgage payment
        mortgage_payment = self.compute_mortgage_payment(
            principal=loan_amount,
            annual_rate=annual_rate,
            amortization_years=amortization_years
        )
        
        # Calculate housing costs (PITH)
        piti = mortgage_payment + monthly_property_tax
        housing_costs = self.compute_housing_costs(
            piti=piti,
            condo_fees=monthly_condo_fees,
            heating=monthly_heating
        )
        
        # Calculate ratios
        gds = self.compute_gds(housing_costs, monthly_income)
        tds = self.compute_tds(housing_costs, other_monthly_debts, monthly_income)
        ltv = self.compute_ltv(loan_amount, property_value)
        
        return {
            "monthly_income": CalculationResult(
                name="monthly_income",
                value=monthly_income,
                inputs={"income_sources": income_sources},
                formula="sum(source.amount * haircut / 12)"
            ),
            "mortgage_payment": CalculationResult(
                name="mortgage_payment",
                value=mortgage_payment,
                inputs={
                    "principal": loan_amount,
                    "annual_rate": annual_rate,
                    "amortization_years": amortization_years
                },
                formula="P * [r(1+r)^n] / [(1+r)^n - 1]"
            ),
            "housing_costs": CalculationResult(
                name="housing_costs",
                value=housing_costs,
                inputs={
                    "piti": piti,
                    "condo_fees": monthly_condo_fees,
                    "heating": monthly_heating
                },
                formula="PITI + (condo_fees * 0.5) + heating"
            ),
            "gds": CalculationResult(
                name="gds",
                value=gds,
                inputs={"housing_costs": housing_costs, "monthly_income": monthly_income},
                formula="housing_costs / monthly_income"
            ),
            "tds": CalculationResult(
                name="tds",
                value=tds,
                inputs={
                    "housing_costs": housing_costs,
                    "other_debts": other_monthly_debts,
                    "monthly_income": monthly_income
                },
                formula="(housing_costs + other_debts) / monthly_income"
            ),
            "ltv": CalculationResult(
                name="ltv",
                value=ltv,
                inputs={"loan_amount": loan_amount, "property_value": property_value},
                formula="loan_amount / property_value"
            )
        }
