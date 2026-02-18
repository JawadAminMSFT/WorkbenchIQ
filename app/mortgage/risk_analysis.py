"""
Risk Analysis Service for Mortgage Underwriting.

Provides comprehensive risk assessment including:
- Income consistency verification
- Fraud signal detection
- AML (Anti-Money Laundering) triage
- Credit risk analysis
- Risk signal aggregation
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import re


class RiskSeverity(str, Enum):
    """Risk signal severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskCategory(str, Enum):
    """Risk signal categories."""
    INCOME = "income"
    FRAUD = "fraud"
    AML = "aml"
    CREDIT = "credit"
    PROPERTY = "property"


@dataclass
class RiskSignal:
    """
    Individual risk signal from analysis.
    
    Contains category, severity, description, and evidence trail.
    """
    category: str
    severity: str
    description: str
    source_documents: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    weight: int = 1
    
    def __post_init__(self):
        # Set weight based on severity if not explicitly set
        if self.weight == 1:
            severity_weights = {"low": 1, "medium": 2, "high": 5}
            self.weight = severity_weights.get(self.severity, 1)


@dataclass
class RiskReport:
    """
    Aggregated risk analysis report.
    
    Summarizes all risk signals with overall score and recommendations.
    """
    overall_score: float
    risk_level: str
    signals: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConsistencyResult:
    """Result of income consistency check."""
    is_consistent: bool
    discrepancies: List[RiskSignal] = field(default_factory=list)
    verified_income: float = 0.0
    stated_income: float = 0.0
    variance_percent: float = 0.0


@dataclass
class CreditDepthResult:
    """Result of credit depth analysis."""
    thin_file: bool
    trade_line_count: int
    oldest_trade_months: int
    risk_level: str


@dataclass
class UtilizationResult:
    """Result of credit utilization check."""
    has_high_utilization: bool
    average_utilization: float
    max_utilization: float
    cards_over_threshold: int


@dataclass
class DownPaymentResult:
    """Result of down payment source check."""
    risk_level: str
    source_verified: bool
    concerns: List[str] = field(default_factory=list)


@dataclass
class GiftComplianceResult:
    """Result of gift letter compliance check."""
    compliant: bool
    issues: List[str] = field(default_factory=list)


class IncomeConsistencyEngine:
    """
    Verifies income consistency across multiple documents.
    
    Compares stated income against T4, pay stubs, and employment letters.
    """
    
    DEFAULT_VARIANCE_THRESHOLD = 0.15  # 15% variance allowed
    
    def __init__(self):
        """Initialize income consistency engine."""
        pass
    
    def check_consistency(
        self,
        income_data: Dict[str, Any],
        variance_threshold: float = None
    ) -> ConsistencyResult:
        """
        Check income consistency across documents.
        
        Args:
            income_data: Dictionary with income from various sources
            variance_threshold: Maximum allowed variance (default 15%)
            
        Returns:
            ConsistencyResult with discrepancies if any
        """
        threshold = variance_threshold or self.DEFAULT_VARIANCE_THRESHOLD
        discrepancies = []
        
        # Get stated income from application
        application = income_data.get("application", {})
        stated_income = application.get("stated_annual_income", 0)
        
        # Collect verified incomes from documents
        verified_incomes = []
        
        # Check T4
        t4 = income_data.get("t4", {})
        if t4.get("income"):
            verified_incomes.append(("T4", t4["income"]))
        
        # Check employment letter
        emp_letter = income_data.get("employment_letter", {})
        if emp_letter.get("annual_salary"):
            verified_incomes.append(("Employment Letter", emp_letter["annual_salary"]))
        
        # Check paystub - project to annual
        paystub = income_data.get("paystub", {})
        if paystub.get("ytd_gross") and paystub.get("pay_date"):
            projected = self.project_annual_income(
                paystub["ytd_gross"],
                paystub["pay_date"]
            )
            verified_incomes.append(("Paystub (projected)", projected))
        
        # Calculate average verified income
        if verified_incomes:
            avg_verified = sum(v[1] for v in verified_incomes) / len(verified_incomes)
        else:
            avg_verified = stated_income
        
        # Check for discrepancies
        for doc_name, doc_income in verified_incomes:
            variance = self.calculate_variance(stated_income, doc_income)
            
            if abs(variance) > threshold:
                severity = "high" if abs(variance) > threshold * 2 else "medium"
                discrepancies.append(RiskSignal(
                    category="income",
                    severity=severity,
                    description=f"Income variance {variance:.1%} between stated and {doc_name}",
                    source_documents=[doc_name.lower().replace(" ", "_")],
                    evidence={
                        "stated_income": stated_income,
                        "document_income": doc_income,
                        "variance": variance
                    }
                ))
        
        # Check consistency between verified sources
        if len(verified_incomes) > 1:
            incomes = [v[1] for v in verified_incomes]
            max_income = max(incomes)
            min_income = min(incomes)
            if min_income > 0:
                source_variance = (max_income - min_income) / min_income
                if source_variance > threshold:
                    discrepancies.append(RiskSignal(
                        category="income",
                        severity="medium",
                        description=f"Income variance {source_variance:.1%} between verification sources",
                        source_documents=[v[0].lower().replace(" ", "_") for v in verified_incomes],
                        evidence={
                            "max_income": max_income,
                            "min_income": min_income,
                            "variance": source_variance
                        }
                    ))
        
        variance_percent = self.calculate_variance(stated_income, avg_verified) if avg_verified else 0
        
        return ConsistencyResult(
            is_consistent=len(discrepancies) == 0,
            discrepancies=discrepancies,
            verified_income=avg_verified,
            stated_income=stated_income,
            variance_percent=variance_percent
        )
    
    def calculate_variance(self, stated: float, verified: float) -> float:
        """
        Calculate variance between stated and verified income.
        
        Args:
            stated: Stated income amount
            verified: Verified income amount
            
        Returns:
            Variance as decimal (e.g., 0.20 for 20%)
        """
        if verified == 0:
            return 0.0
        return round((stated - verified) / verified, 2)
    
    def project_annual_income(self, ytd_gross: float, pay_date: str) -> float:
        """
        Project YTD income to annual amount.
        
        Args:
            ytd_gross: Year-to-date gross income
            pay_date: Date of the pay stub (YYYY-MM-DD)
            
        Returns:
            Projected annual income
        """
        try:
            if isinstance(pay_date, str):
                pay_dt = datetime.strptime(pay_date, "%Y-%m-%d")
            else:
                pay_dt = pay_date
            
            # Calculate days elapsed in year
            year_start = datetime(pay_dt.year, 1, 1)
            days_elapsed = (pay_dt - year_start).days + 1
            
            if days_elapsed <= 0:
                return ytd_gross
            
            # Project to full year
            daily_rate = ytd_gross / days_elapsed
            projected = daily_rate * 365
            
            return round(projected, 2)
        except (ValueError, TypeError):
            return ytd_gross


class FraudDetectionEngine:
    """
    Detects potential fraud signals in mortgage applications.
    
    Checks for income manipulation, employment discrepancies,
    property flip schemes, and straw buyer indicators.
    """
    
    def __init__(self):
        """Initialize fraud detection engine."""
        pass
    
    def analyze_income(self, income_data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Analyze income for fraud signals.
        
        Args:
            income_data: Income information
            
        Returns:
            List of risk signals
        """
        signals = []
        
        annual_income = income_data.get("annual_income", 0)
        
        # Check for suspiciously round numbers (exact thousands)
        if annual_income > 0 and annual_income % 10000 == 0:
            signals.append(RiskSignal(
                category="fraud",
                severity="low",
                description="Income is a round number - may warrant verification",
                evidence={"annual_income": annual_income}
            ))
        
        return signals
    
    def check_employment_consistency(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Check employment information consistency.
        
        Args:
            data: Employment data from application and documents
            
        Returns:
            List of risk signals
        """
        signals = []
        
        application = data.get("application", {})
        emp_letter = data.get("employment_letter", {})
        current_date_str = data.get("current_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Parse dates
        try:
            start_date_str = application.get("employer_start_date", "")
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
                
                # Calculate actual tenure
                actual_months = (current_date - start_date).days / 30.44
                actual_years = actual_months / 12
                
                # Parse stated tenure from employment letter
                tenure_str = emp_letter.get("tenure", "")
                stated_years = self._parse_tenure(tenure_str)
                
                if stated_years > 0:
                    variance = abs(actual_years - stated_years)
                    
                    if variance > 1.5:  # More than 1.5 years difference
                        signals.append(RiskSignal(
                            category="fraud",
                            severity="high",
                            description=f"Employment tenure discrepancy: {actual_years:.1f} years actual vs {stated_years} years stated",
                            source_documents=["application", "employment_letter"],
                            evidence={
                                "actual_years": round(actual_years, 1),
                                "stated_years": stated_years,
                                "variance_years": round(variance, 1)
                            }
                        ))
                    elif variance > 0.5:
                        signals.append(RiskSignal(
                            category="fraud",
                            severity="low",
                            description=f"Minor employment tenure variance: {variance:.1f} years",
                            evidence={
                                "actual_years": round(actual_years, 1),
                                "stated_years": stated_years
                            }
                        ))
        except (ValueError, TypeError):
            pass
        
        return signals
    
    def _parse_tenure(self, tenure_str: str) -> float:
        """Parse tenure string like '5 years' to float."""
        if not tenure_str:
            return 0.0
        
        # Extract number from string
        match = re.search(r'(\d+(?:\.\d+)?)', tenure_str)
        if match:
            return float(match.group(1))
        return 0.0
    
    def check_property_flip(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Detect potential property flipping.
        
        Args:
            data: Property transaction data
            
        Returns:
            List of risk signals
        """
        signals = []
        
        prop = data.get("property", {})
        last_sale_date_str = prop.get("last_sale_date", "")
        last_sale_price = prop.get("last_sale_price", 0)
        current_price = prop.get("current_purchase_price", 0)
        appraisal_date_str = prop.get("appraisal_date", "")
        
        if last_sale_date_str and last_sale_price and current_price:
            try:
                last_sale = datetime.strptime(last_sale_date_str, "%Y-%m-%d")
                appraisal = datetime.strptime(appraisal_date_str, "%Y-%m-%d") if appraisal_date_str else datetime.now()
                
                months_between = (appraisal - last_sale).days / 30.44
                price_increase = (current_price - last_sale_price) / last_sale_price if last_sale_price else 0
                
                # Flag if >20% increase in less than 6 months
                if months_between < 6 and price_increase > 0.20:
                    signals.append(RiskSignal(
                        category="fraud",
                        severity="high",
                        description=f"Potential property flip: {price_increase:.0%} increase in {months_between:.0f} months",
                        source_documents=["title_search", "appraisal"],
                        evidence={
                            "months_since_last_sale": round(months_between, 1),
                            "price_increase_pct": round(price_increase, 2),
                            "last_sale_price": last_sale_price,
                            "current_price": current_price
                        }
                    ))
                elif months_between < 12 and price_increase > 0.15:
                    signals.append(RiskSignal(
                        category="fraud",
                        severity="medium",
                        description=f"Recent property resale with {price_increase:.0%} increase",
                        evidence={
                            "months_since_last_sale": round(months_between, 1),
                            "price_increase_pct": round(price_increase, 2)
                        }
                    ))
            except (ValueError, TypeError):
                pass
        
        return signals
    
    def check_straw_buyer_risk(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Check for straw buyer indicators.
        
        Args:
            data: Borrower and property data
            
        Returns:
            List of risk signals
        """
        signals = []
        
        borrower = data.get("borrower", {})
        prop = data.get("property", {})
        
        income = borrower.get("income", 0)
        down_payment_source = borrower.get("down_payment_source", "").lower()
        gift_amount = borrower.get("gift_amount", 0)
        property_price = prop.get("price", 0)
        occupancy = prop.get("occupancy", "").lower()
        
        # Check gift relative to income
        if gift_amount > 0 and income > 0:
            gift_to_income_ratio = gift_amount / income
            
            if gift_to_income_ratio > 3:  # Gift is >3x annual income
                signals.append(RiskSignal(
                    category="fraud",
                    severity="medium",
                    description=f"Large gift ({gift_to_income_ratio:.1f}x annual income) may indicate straw buyer",
                    source_documents=["application", "gift_letter"],
                    evidence={
                        "gift_amount": gift_amount,
                        "annual_income": income,
                        "gift_to_income_ratio": round(gift_to_income_ratio, 2)
                    }
                ))
        
        # Check if property is stated as owner-occupied but indicators suggest otherwise
        if occupancy == "owner_occupied" and property_price > 0 and income > 0:
            price_to_income = property_price / income
            if price_to_income > 15:  # Property is >15x income
                signals.append(RiskSignal(
                    category="fraud",
                    severity="low",
                    description="High property-to-income ratio warrants occupancy verification",
                    evidence={
                        "property_price": property_price,
                        "income": income,
                        "price_to_income": round(price_to_income, 1)
                    }
                ))
        
        return signals


class AMLTriageEngine:
    """
    Anti-Money Laundering triage and risk assessment.
    
    Checks down payment sources, deposit patterns, gift compliance,
    and transaction relationships.
    """
    
    CASH_THRESHOLD = 10000  # FINTRAC reporting threshold
    
    def __init__(self):
        """Initialize AML triage engine."""
        pass
    
    def check_down_payment_source(self, data: Dict[str, Any]) -> DownPaymentResult:
        """
        Verify down payment source documentation.
        
        Args:
            data: Down payment source information
            
        Returns:
            DownPaymentResult with risk level
        """
        concerns = []
        
        source = data.get("source", "").lower()
        months_documented = data.get("bank_statements_months", 0)
        accumulation = data.get("accumulation_pattern", "").lower()
        down_payment = data.get("down_payment", 0)
        
        # Check documentation period
        if months_documented < 3:
            concerns.append("Less than 3 months of bank statements provided")
        
        # Check accumulation pattern
        if accumulation == "sudden" or accumulation == "recent":
            concerns.append("Sudden accumulation of down payment funds")
        
        # Check source type
        if source in ["cash", "unknown", "other"]:
            concerns.append(f"Down payment source '{source}' requires additional verification")
        
        # Determine risk level
        if len(concerns) >= 2:
            risk_level = "high"
        elif len(concerns) == 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return DownPaymentResult(
            risk_level=risk_level,
            source_verified=source in ["savings", "rrsp", "sale_of_property", "gift"],
            concerns=concerns
        )
    
    def analyze_deposits(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Analyze bank statement deposits for AML signals.
        
        Args:
            data: Bank statement transaction data
            
        Returns:
            List of risk signals
        """
        signals = []
        
        transactions = data.get("bank_statement_transactions", [])
        
        # Find large cash deposits
        cash_deposits = [
            t for t in transactions
            if t.get("type") == "deposit" and 
            "cash" in t.get("description", "").lower()
        ]
        
        total_cash = sum(t.get("amount", 0) for t in cash_deposits)
        
        if cash_deposits:
            max_cash = max(t.get("amount", 0) for t in cash_deposits)
            
            if max_cash >= self.CASH_THRESHOLD:
                signals.append(RiskSignal(
                    category="aml",
                    severity="high",
                    description=f"Large cash deposit of ${max_cash:,.0f} exceeds FINTRAC threshold",
                    source_documents=["bank_statement"],
                    evidence={
                        "max_cash_deposit": max_cash,
                        "total_cash_deposits": total_cash,
                        "cash_deposit_count": len(cash_deposits)
                    }
                ))
            elif total_cash > self.CASH_THRESHOLD:
                signals.append(RiskSignal(
                    category="aml",
                    severity="medium",
                    description=f"Multiple cash deposits totaling ${total_cash:,.0f}",
                    source_documents=["bank_statement"],
                    evidence={
                        "total_cash_deposits": total_cash,
                        "cash_deposit_count": len(cash_deposits)
                    }
                ))
        
        return signals
    
    def detect_structuring(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Detect potential structuring (deposits just under threshold).
        
        Args:
            data: Bank statement transaction data
            
        Returns:
            List of risk signals
        """
        signals = []
        
        transactions = data.get("bank_statement_transactions", [])
        
        # Find deposits just under $10K threshold
        suspicious_deposits = [
            t for t in transactions
            if t.get("type") == "deposit" and
            8000 <= t.get("amount", 0) < self.CASH_THRESHOLD
        ]
        
        if len(suspicious_deposits) >= 3:
            total = sum(t.get("amount", 0) for t in suspicious_deposits)
            signals.append(RiskSignal(
                category="aml",
                severity="high",
                description=f"Potential structuring: {len(suspicious_deposits)} deposits between $8K-$10K",
                source_documents=["bank_statement"],
                evidence={
                    "deposit_count": len(suspicious_deposits),
                    "total_amount": total,
                    "deposits": [t.get("amount") for t in suspicious_deposits]
                }
            ))
        elif len(suspicious_deposits) >= 2:
            signals.append(RiskSignal(
                category="aml",
                severity="medium",
                description=f"Multiple deposits just under reporting threshold",
                source_documents=["bank_statement"],
                evidence={
                    "deposit_count": len(suspicious_deposits)
                }
            ))
        
        return signals
    
    def check_gift_compliance(self, data: Dict[str, Any]) -> GiftComplianceResult:
        """
        Verify gift letter requirements.
        
        Args:
            data: Gift information
            
        Returns:
            GiftComplianceResult with compliance status
        """
        issues = []
        
        relationship = data.get("donor_relationship", "").lower()
        account_verified = data.get("donor_account_verified", False)
        repayment_required = data.get("repayment_required", True)
        gift_amount = data.get("gift_amount", 0)
        
        # Check relationship
        if relationship not in ["parent", "grandparent", "sibling", "spouse", "family"]:
            issues.append(f"Gift from '{relationship}' may not qualify as acceptable gift")
        
        # Check account verification
        if not account_verified and gift_amount >= 10000:
            issues.append("Donor account not verified for large gift")
        
        # Check repayment requirement
        if repayment_required:
            issues.append("Gift letter indicates repayment - may be treated as loan")
        
        return GiftComplianceResult(
            compliant=len(issues) == 0,
            issues=issues
        )
    
    def check_arms_length(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Check for non-arm's length transaction issues.
        
        Args:
            data: Transaction relationship data
            
        Returns:
            List of risk signals
        """
        signals = []
        
        relationship = data.get("seller_relationship", "").lower()
        purchase_price = data.get("purchase_price", 0)
        appraisal_value = data.get("appraisal_value", 0)
        
        # Check if related party transaction
        if relationship in ["family_member", "related", "employer", "business_partner"]:
            signals.append(RiskSignal(
                category="aml",
                severity="medium",
                description=f"Non-arm's length transaction with {relationship}",
                source_documents=["purchase_agreement"],
                evidence={
                    "seller_relationship": relationship,
                    "purchase_price": purchase_price,
                    "appraisal_value": appraisal_value
                }
            ))
            
            # Check if below market value
            if purchase_price < appraisal_value and appraisal_value > 0:
                discount = (appraisal_value - purchase_price) / appraisal_value
                if discount > 0.10:  # More than 10% below appraisal
                    signals.append(RiskSignal(
                        category="aml",
                        severity="high",
                        description=f"Below-market purchase ({discount:.0%} discount) from related party",
                        source_documents=["purchase_agreement", "appraisal"],
                        evidence={
                            "discount_percent": round(discount, 2),
                            "purchase_price": purchase_price,
                            "appraisal_value": appraisal_value
                        }
                    ))
        
        return signals


class CreditRiskEngine:
    """
    Credit risk analysis and scoring.
    
    Analyzes credit scores, trade lines, derogatory items,
    and credit utilization.
    """
    
    # Credit score thresholds
    EXCELLENT_THRESHOLD = 760
    GOOD_THRESHOLD = 700
    FAIR_THRESHOLD = 650
    POOR_THRESHOLD = 600
    
    # Thin file thresholds
    MIN_TRADE_LINES = 3
    MIN_CREDIT_HISTORY_MONTHS = 24
    
    # Utilization threshold
    HIGH_UTILIZATION_THRESHOLD = 0.75
    
    def __init__(self):
        """Initialize credit risk engine."""
        pass
    
    def categorize_score(self, score: int) -> str:
        """
        Categorize credit score.
        
        Args:
            score: Credit bureau score
            
        Returns:
            Category string (excellent, good, fair, poor, very_poor)
        """
        if score >= self.EXCELLENT_THRESHOLD:
            return "excellent"
        elif score >= self.GOOD_THRESHOLD:
            return "good"
        elif score >= self.FAIR_THRESHOLD:
            return "fair"
        elif score >= self.POOR_THRESHOLD:
            return "poor"
        else:
            return "very_poor"
    
    def analyze_credit_depth(self, data: Dict[str, Any]) -> CreditDepthResult:
        """
        Analyze credit file depth.
        
        Args:
            data: Credit data with trade lines and history
            
        Returns:
            CreditDepthResult with thin file indicator
        """
        trade_lines = data.get("trade_lines", 0)
        oldest_trade_months = data.get("oldest_trade_months", 0)
        credit_score = data.get("credit_score", 0)
        
        thin_file = (
            trade_lines < self.MIN_TRADE_LINES or
            oldest_trade_months < self.MIN_CREDIT_HISTORY_MONTHS
        )
        
        if thin_file:
            risk_level = "high" if trade_lines <= 1 else "medium"
        else:
            risk_level = "low"
        
        return CreditDepthResult(
            thin_file=thin_file,
            trade_line_count=trade_lines,
            oldest_trade_months=oldest_trade_months,
            risk_level=risk_level
        )
    
    def check_derogatory_items(self, data: Dict[str, Any]) -> List[RiskSignal]:
        """
        Check for derogatory credit items.
        
        Args:
            data: Credit data with derogatory items
            
        Returns:
            List of risk signals
        """
        signals = []
        
        derogatory_items = data.get("derogatory_items", [])
        
        for item in derogatory_items:
            item_type = item.get("type", "unknown")
            months_ago = item.get("months_ago", 999)
            
            if months_ago <= 12:
                severity = "high"
                desc = f"Recent {item_type.replace('_', ' ')} ({months_ago} months ago)"
            elif months_ago <= 24:
                severity = "medium"
                desc = f"{item_type.replace('_', ' ')} within last 2 years"
            else:
                severity = "low"
                desc = f"Historical {item_type.replace('_', ' ')} ({months_ago} months ago)"
            
            signals.append(RiskSignal(
                category="credit",
                severity=severity,
                description=desc,
                source_documents=["credit_report"],
                evidence={
                    "type": item_type,
                    "months_ago": months_ago
                }
            ))
        
        return signals
    
    def check_utilization(self, data: Dict[str, Any]) -> UtilizationResult:
        """
        Check credit card utilization.
        
        Args:
            data: Credit card data with limits and balances
            
        Returns:
            UtilizationResult with high utilization indicator
        """
        credit_cards = data.get("credit_cards", [])
        
        if not credit_cards:
            return UtilizationResult(
                has_high_utilization=False,
                average_utilization=0.0,
                max_utilization=0.0,
                cards_over_threshold=0
            )
        
        utilizations = []
        for card in credit_cards:
            limit = card.get("limit", 0)
            balance = card.get("balance", 0)
            if limit > 0:
                utilizations.append(balance / limit)
        
        if not utilizations:
            return UtilizationResult(
                has_high_utilization=False,
                average_utilization=0.0,
                max_utilization=0.0,
                cards_over_threshold=0
            )
        
        avg_util = sum(utilizations) / len(utilizations)
        max_util = max(utilizations)
        over_threshold = sum(1 for u in utilizations if u > self.HIGH_UTILIZATION_THRESHOLD)
        
        return UtilizationResult(
            has_high_utilization=max_util > self.HIGH_UTILIZATION_THRESHOLD,
            average_utilization=round(avg_util, 2),
            max_utilization=round(max_util, 2),
            cards_over_threshold=over_threshold
        )


class RiskSignalAggregator:
    """
    Aggregates risk signals from all engines and computes overall risk score.
    """
    
    # Risk score thresholds
    LOW_RISK_THRESHOLD = 25
    MEDIUM_RISK_THRESHOLD = 50
    
    def __init__(self):
        """Initialize risk signal aggregator."""
        pass
    
    def aggregate(
        self,
        income_signals: List[RiskSignal],
        fraud_signals: List[RiskSignal],
        aml_signals: List[RiskSignal],
        credit_signals: List[RiskSignal]
    ) -> 'AggregatedResult':
        """
        Aggregate signals from all risk engines.
        
        Args:
            income_signals: Signals from income consistency engine
            fraud_signals: Signals from fraud detection engine
            aml_signals: Signals from AML triage engine
            credit_signals: Signals from credit risk engine
            
        Returns:
            AggregatedResult with total count and categorization
        """
        all_signals = income_signals + fraud_signals + aml_signals + credit_signals
        
        return AggregatedResult(
            total_signals=len(all_signals),
            by_category={
                "income": len(income_signals),
                "fraud": len(fraud_signals),
                "aml": len(aml_signals),
                "credit": len(credit_signals)
            },
            signals=all_signals
        )
    
    def compute_risk_score(self, signals: List[RiskSignal]) -> float:
        """
        Compute overall risk score from signals.
        
        Args:
            signals: List of all risk signals
            
        Returns:
            Risk score from 0-100
        """
        if not signals:
            return 0.0
        
        # Calculate weighted sum
        total_weight = sum(s.weight for s in signals)
        
        # Normalize to 0-100 scale (cap at 10 high-severity signals worth)
        max_expected_weight = 50  # 10 high signals * 5 weight
        score = min(100, (total_weight / max_expected_weight) * 100)
        
        return round(score, 1)
    
    def categorize_risk(self, score: float) -> str:
        """
        Categorize risk level from score.
        
        Args:
            score: Risk score 0-100
            
        Returns:
            Risk level string
        """
        if score <= self.LOW_RISK_THRESHOLD:
            return "low"
        elif score <= self.MEDIUM_RISK_THRESHOLD:
            return "medium"
        else:
            return "high"
    
    def generate_summary(self, signals: List[RiskSignal]) -> str:
        """
        Generate human-readable risk summary.
        
        Args:
            signals: List of risk signals
            
        Returns:
            Summary text
        """
        if not signals:
            return "No risk signals detected. Application appears low risk."
        
        # Group by category
        by_category = {}
        for s in signals:
            category = s.category if isinstance(s.category, str) else s.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(s)
        
        # Build summary
        lines = [f"Risk analysis identified {len(signals)} signal(s):"]
        
        for category, cat_signals in by_category.items():
            high_count = sum(1 for s in cat_signals if s.severity == "high")
            lines.append(f"- {category.capitalize()}: {len(cat_signals)} signal(s), {high_count} high severity")
        
        # Add top concerns
        high_signals = [s for s in signals if s.severity == "high"]
        if high_signals:
            lines.append("\nKey concerns:")
            for s in high_signals[:3]:  # Top 3 high severity
                desc = s.description if isinstance(s.description, str) else s.description
                lines.append(f"  • {desc}")
        
        return "\n".join(lines)
    
    def generate_report(self, signals: List[RiskSignal]) -> RiskReport:
        """
        Generate complete risk report.
        
        Args:
            signals: All risk signals
            
        Returns:
            RiskReport with score, level, and recommendations
        """
        score = self.compute_risk_score(signals)
        level = self.categorize_risk(score)
        
        # Generate recommendations based on signals
        recommendations = []
        
        has_income_signals = any(s.category == "income" for s in signals)
        has_fraud_signals = any(s.category == "fraud" and s.severity == "high" for s in signals)
        has_aml_signals = any(s.category == "aml" for s in signals)
        has_credit_signals = any(s.category == "credit" and s.severity == "high" for s in signals)
        
        if has_income_signals:
            recommendations.append("Verify employment with verbal VOE")
            recommendations.append("Request additional income documentation")
        
        if has_fraud_signals:
            recommendations.append("Escalate to fraud investigation team")
        
        if has_aml_signals:
            recommendations.append("Request additional bank statements")
            recommendations.append("Verify source of down payment funds")
        
        if has_credit_signals:
            recommendations.append("Request explanation for derogatory items")
        
        if not recommendations:
            recommendations.append("Standard underwriting review")
        
        return RiskReport(
            overall_score=score,
            risk_level=level,
            signals=[{"id": f"sig_{i:03d}", "category": s.category, "severity": s.severity, "description": s.description} for i, s in enumerate(signals, 1)],
            recommendations=recommendations
        )


@dataclass
class AggregatedResult:
    """Result of signal aggregation."""
    total_signals: int
    by_category: Dict[str, int]
    signals: List[RiskSignal]
