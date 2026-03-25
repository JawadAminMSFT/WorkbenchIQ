"""Rich, realistic seed data for 3 mortgage underwriting applications.

Each application aligns with the Customer 360 narratives for
Sarah Chen, Marcus Williams, and Priya Patel.
"""

from __future__ import annotations

from typing import Any


def _sarah_chen_app() -> dict[str, Any]:
    """Conventional mortgage — approved, no conditions."""
    return {
        "id": "app-sc-mtg-001",
        "created_at": "2021-09-12T14:32:00Z",
        "external_reference": "CUST-SC-001",
        "status": "completed",
        "persona": "mortgage_underwriting",
        "files": [],
        "processing_status": "idle",
        "llm_outputs": {
            "application_summary": {
                "borrower_profile": {
                    "section": "application_summary",
                    "subsection": "borrower_profile",
                    "raw": (
                        "Sarah Chen (DOB 1988-03-15) and co-borrower David Chen "
                        "(DOB 1986-07-22) are applying for a conventional mortgage "
                        "to purchase a detached home at 42 Maple Grove Ave, Toronto, "
                        "ON M4C 1L8. Sarah is a Senior Software Engineer at "
                        "TechStream Solutions earning $105,000/yr (permanent "
                        "full-time since June 2017). David is a Marketing Manager "
                        "at BrightPath Media earning $80,000/yr (permanent "
                        "full-time since March 2019). Combined household income is "
                        "$185,000/yr. Sarah's credit score is 780 (Equifax) and "
                        "David's is 755 (Equifax). They have minimal existing debt "
                        "— two revolving credit accounts with total monthly "
                        "obligations of $250. The property is a detached house "
                        "listed at $650,000 with an appraised value of $660,000. "
                        "They are putting $130,000 down (20%) from personal "
                        "savings, resulting in an LTV of 80%. Banking records at "
                        "TD Canada Trust show a stable average monthly balance of "
                        "$45,200 with an ending balance of $142,500 and zero "
                        "NSF/overdraft events."
                    ),
                    "parsed": {
                        "borrowers": [
                            {
                                "name": "Sarah Chen",
                                "date_of_birth": "1988-03-15",
                                "SIN": None,
                                "credit_score": 780,
                                "employment": {
                                    "employer": "TechStream Solutions",
                                    "position": "Senior Software Engineer",
                                    "status": "Permanent full-time",
                                    "start_date": "2017-06-01",
                                    "annual_base_salary_CAD": 105000,
                                    "other_compensation_CAD": 0,
                                    "total_employment_income_2021_CAD": 105000,
                                    "net_income_2020_CAD": 98000,
                                },
                                "income_sources": [
                                    {
                                        "type": "Employment",
                                        "employer": "TechStream Solutions",
                                        "annual_income_CAD": 105000,
                                    },
                                ],
                                "existing_debts_and_liabilities": {
                                    "open_revolving_accounts": 2,
                                    "installment_loans": "None",
                                    "derogatory_items": "None",
                                    "total_monthly_debt_obligations_CAD": 250,
                                },
                            },
                            {
                                "name": "David Chen",
                                "date_of_birth": "1986-07-22",
                                "SIN": None,
                                "credit_score": 755,
                                "employment": {
                                    "employer": "BrightPath Media",
                                    "position": "Marketing Manager",
                                    "status": "Permanent full-time",
                                    "start_date": "2019-03-15",
                                    "annual_base_salary_CAD": 80000,
                                    "other_compensation_CAD": 0,
                                    "total_employment_income_2021_CAD": 80000,
                                    "net_income_2020_CAD": 74500,
                                },
                                "income_sources": [
                                    {
                                        "type": "Employment",
                                        "employer": "BrightPath Media",
                                        "annual_income_CAD": 80000,
                                    },
                                ],
                                "existing_debts_and_liabilities": {
                                    "open_revolving_accounts": 1,
                                    "installment_loans": "None",
                                    "derogatory_items": "None",
                                    "total_monthly_debt_obligations_CAD": 0,
                                },
                            },
                        ],
                        "property": {
                            "address": "42 Maple Grove Ave, Toronto, ON M4C 1L8",
                            "type": "Detached house",
                            "occupancy": "Owner-occupied (Primary residence)",
                            "purchase_price_CAD": 650000,
                            "appraised_value_CAD": 660000,
                            "deposit_paid_CAD": 25000,
                            "market_conditions": "Stable",
                            "observed_condition": "Good",
                        },
                        "loan": {
                            "requested_mortgage_CAD": 520000,
                            "LTV_percent": 80.0,
                            "rate": "3.49% Fixed",
                            "term_years": 5,
                            "amortization_years": 25,
                            "down_payment_CAD": 130000,
                            "down_payment_sources": [
                                {"type": "Savings", "amount_CAD": 130000},
                            ],
                            "closing_date": "2021-11-15",
                        },
                        "banking": {
                            "institution": "TD Canada Trust",
                            "account_masked": "******4521",
                            "avg_monthly_balance_CAD": 45200,
                            "ending_balance_CAD": 142500,
                            "largest_single_deposit_CAD": 8500,
                            "NSF_overdraft_events": 0,
                            "down_payment_funds_observed": True,
                        },
                    },
                },
                "ratio_calculation": {
                    "section": "application_summary",
                    "subsection": "ratio_calculation",
                    "raw": (
                        "Gross Debt Service (GDS) ratio calculated at 28.0%, well "
                        "within the 39% OSFI B-20 guideline. Total Debt Service "
                        "(TDS) ratio calculated at 35.0%, within the 44% limit. "
                        "Monthly housing costs (mortgage P&I $2,610, property tax "
                        "$542, heating $167) total $3,319. Combined gross monthly "
                        "income is $15,417. Monthly debt obligations of $250 bring "
                        "total obligations to $3,569 for TDS purposes. Stress test "
                        "at qualifying rate of 5.25% yields GDS of 33.2% and TDS "
                        "of 40.1%, both within limits."
                    ),
                    "parsed": {
                        "GDS": 28.0,
                        "TDS": 35.0,
                        "GDS_status": "Acceptable",
                        "TDS_status": "Acceptable",
                        "GDS_limit": 39,
                        "TDS_limit": 44,
                    },
                },
                "income_analysis": {
                    "section": "application_summary",
                    "subsection": "income_analysis",
                    "raw": (
                        "Combined gross household income of $185,000 per annum "
                        "($105,000 primary borrower + $80,000 co-borrower). Both "
                        "borrowers are permanent full-time employees with stable "
                        "tenure — Sarah has been at TechStream Solutions for over "
                        "4 years and David at BrightPath Media for over 2 years. "
                        "Income verified through T4 slips (2019, 2020), recent pay "
                        "stubs (3 months), and employment letters from both "
                        "employers. No income irregularities noted. Average monthly "
                        "gross income of $15,417."
                    ),
                    "parsed": {
                        "total_gross_income_CAD": 185000,
                        "avg_monthly_gross_CAD": 15417,
                        "employment_stability": (
                            "Strong (dual income, permanent FT, >4yr tenure)"
                        ),
                        "income_verification": (
                            "Verified via T4s, pay stubs, employment letters"
                        ),
                    },
                },
                "risk_assessment": {
                    "section": "application_summary",
                    "subsection": "risk_assessment",
                    "raw": (
                        "Overall risk profile is LOW. Credit risk is low — primary "
                        "borrower has a credit score of 780 and co-borrower 755, "
                        "both well above the 680 threshold. Employment risk is low "
                        "with stable dual income from permanent full-time "
                        "positions. Property risk is low — detached house in an "
                        "established Toronto neighbourhood with stable market "
                        "conditions and appraisal at or above purchase price. Debt "
                        "risk is low with minimal existing obligations ($250/mo). "
                        "Liquidity risk is low with $142,500 ending balance in "
                        "savings, well above down payment and closing costs."
                    ),
                    "parsed": {
                        "overall_risk": "Low",
                        "credit_risk": "Low (credit score 780)",
                        "employment_risk": "Low (stable dual income)",
                        "property_risk": "Low (detached house, stable market)",
                        "debt_risk": "Low (minimal existing debt)",
                        "liquidity_risk": "Low (strong savings balance)",
                    },
                },
                "recommendation": {
                    "section": "application_summary",
                    "subsection": "recommendation",
                    "raw": (
                        "RECOMMENDATION: APPROVE. Strong dual-income household "
                        "with excellent credit scores, conservative 80% LTV, and "
                        "minimal existing debt. All OSFI B-20 guidelines are "
                        "comfortably met including the stress test at the "
                        "qualifying rate. Down payment fully sourced from personal "
                        "savings with no anti-money-laundering concerns. No "
                        "conditions required. Proceed to closing."
                    ),
                    "parsed": {
                        "DECISION": "Approve",
                        "RATIONALE": (
                            "Strong dual income, excellent credit, conservative "
                            "LTV, minimal debt. Well within all OSFI B-20 "
                            "guidelines."
                        ),
                        "CONDITIONS": [],
                        "NEXT_STEPS": [
                            "Standard title insurance",
                            "Final verification of employment",
                            "Close by 2021-11-15",
                        ],
                    },
                },
            },
        },
        "extracted_fields": {
            "application:BorrowerName": {
                "field_name": "BorrowerName",
                "value": "Sarah Chen",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:CoBorrowerName": {
                "field_name": "CoBorrowerName",
                "value": "David Chen",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:BorrowerDOB": {
                "field_name": "BorrowerDOB",
                "value": "1988-03-15",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:CoBorrowerDOB": {
                "field_name": "CoBorrowerDOB",
                "value": "1986-07-22",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:PurchasePrice": {
                "field_name": "PurchasePrice",
                "value": "650000",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:RequestedLoanAmount": {
                "field_name": "RequestedLoanAmount",
                "value": "520000",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyAddress": {
                "field_name": "PropertyAddress",
                "value": "42 Maple Grove Ave, Toronto, ON M4C 1L8",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyType": {
                "field_name": "PropertyType",
                "value": "single_family_detached",
                "confidence": 0.94,
                "source_file": "mortgage_application.pdf",
            },
            "application:LoanToValueRatio": {
                "field_name": "LoanToValueRatio",
                "value": "80.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyOccupancy": {
                "field_name": "PropertyOccupancy",
                "value": "Owner-occupied",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateTerm": {
                "field_name": "RateTerm",
                "value": "5 years Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:AmortizationYears": {
                "field_name": "AmortizationYears",
                "value": 25,
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ContractRate": {
                "field_name": "ContractRate",
                "value": "3.49%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateType": {
                "field_name": "RateType",
                "value": "Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ClosingDate": {
                "field_name": "ClosingDate",
                "value": "2021-11-15",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentAmount": {
                "field_name": "DownPaymentAmount",
                "value": "130000",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentSource": {
                "field_name": "DownPaymentSource",
                "value": "Personal savings",
                "confidence": 0.93,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentPercent": {
                "field_name": "DownPaymentPercent",
                "value": "20.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:InsuranceRequired": {
                "field_name": "InsuranceRequired",
                "value": "No",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "appraisal:AppraisedValue": {
                "field_name": "AppraisedValue",
                "value": "660000",
                "confidence": 0.95,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:PropertyCondition": {
                "field_name": "PropertyCondition",
                "value": "Good",
                "confidence": 0.92,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:MarketConditions": {
                "field_name": "MarketConditions",
                "value": "Stable",
                "confidence": 0.91,
                "source_file": "appraisal_report.pdf",
            },
            "employment_letter:Employer_B1": {
                "field_name": "Employer_B1",
                "value": "TechStream Solutions",
                "confidence": 0.97,
                "source_file": "employment_letter_b1.pdf",
            },
            "employment_letter:Position_B1": {
                "field_name": "Position_B1",
                "value": "Senior Software Engineer",
                "confidence": 0.96,
                "source_file": "employment_letter_b1.pdf",
            },
            "employment_letter_B1:BaseSalary": {
                "field_name": "BaseSalary",
                "value": "105000",
                "confidence": 0.96,
                "source_file": "employment_letter_b1.pdf",
            },
            "employment_letter:EmploymentStatus_B1": {
                "field_name": "EmploymentStatus_B1",
                "value": "Permanent full-time",
                "confidence": 0.96,
                "source_file": "employment_letter_b1.pdf",
            },
            "employment_letter:StartDate_B1": {
                "field_name": "StartDate_B1",
                "value": "2017-06-01",
                "confidence": 0.94,
                "source_file": "employment_letter_b1.pdf",
            },
            "employment_letter:Employer_B2": {
                "field_name": "Employer_B2",
                "value": "BrightPath Media",
                "confidence": 0.96,
                "source_file": "employment_letter_b2.pdf",
            },
            "employment_letter:Position_B2": {
                "field_name": "Position_B2",
                "value": "Marketing Manager",
                "confidence": 0.95,
                "source_file": "employment_letter_b2.pdf",
            },
            "employment_letter_B2:BaseSalary": {
                "field_name": "BaseSalary",
                "value": "80000",
                "confidence": 0.96,
                "source_file": "employment_letter_b2.pdf",
            },
            "T4_B1:AnnualIncome": {
                "field_name": "AnnualIncome",
                "value": "105000",
                "confidence": 0.98,
                "source_file": "t4_b1.pdf",
            },
            "T4_B2:AnnualIncome": {
                "field_name": "AnnualIncome",
                "value": "80000",
                "confidence": 0.98,
                "source_file": "t4_b2.pdf",
            },
            "t4:TaxYear": {
                "field_name": "TaxYear",
                "value": "2020",
                "confidence": 0.99,
                "source_file": "t4_b1.pdf",
            },
            "bank_statement:DownPaymentAmount": {
                "field_name": "DownPaymentAmount",
                "value": "130000",
                "confidence": 0.93,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:Institution": {
                "field_name": "Institution",
                "value": "TD Canada Trust",
                "confidence": 0.97,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:EndingBalance": {
                "field_name": "EndingBalance",
                "value": "142500",
                "confidence": 0.94,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:AvgMonthlyBalance": {
                "field_name": "AvgMonthlyBalance",
                "value": "45200",
                "confidence": 0.92,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:NSFEvents": {
                "field_name": "NSFEvents",
                "value": "0",
                "confidence": 0.96,
                "source_file": "bank_statements.pdf",
            },
            "credit_report:CreditScore": {
                "field_name": "CreditScore",
                "value": "780",
                "confidence": 0.99,
                "source_file": "credit_report.pdf",
            },
            "credit_report:CreditScore_B2": {
                "field_name": "CreditScore_B2",
                "value": "755",
                "confidence": 0.99,
                "source_file": "credit_report.pdf",
            },
            "credit_report:RevolvingAccounts": {
                "field_name": "RevolvingAccounts",
                "value": "2",
                "confidence": 0.97,
                "source_file": "credit_report.pdf",
            },
            "credit_report:MonthlyDebtObligations": {
                "field_name": "MonthlyDebtObligations",
                "value": "250",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "credit_report:DerogatoryItems": {
                "field_name": "DerogatoryItems",
                "value": "None",
                "confidence": 0.98,
                "source_file": "credit_report.pdf",
            },
            "credit_report:OtherDebtsMonthly": {
                "field_name": "OtherDebtsMonthly",
                "value": "250",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "application:PropertyTaxesAnnual": {
                "field_name": "PropertyTaxesAnnual",
                "value": "6500",
                "confidence": 0.93,
                "source_file": "mortgage_application.pdf",
            },
            "application:HeatingMonthly": {
                "field_name": "HeatingMonthly",
                "value": "150",
                "confidence": 0.92,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmployerName": {
                "field_name": "EmployerName",
                "value": "TechStream Solutions",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:OccupationTitle": {
                "field_name": "OccupationTitle",
                "value": "Senior Software Engineer",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmploymentStatus": {
                "field_name": "EmploymentStatus",
                "value": "Permanent full-time",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:QualifyingRate": {
                "field_name": "QualifyingRate",
                "value": "5.25%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
        },
        "confidence_summary": {
            "total_fields": 48,
            "average_confidence": 0.96,
            "high_confidence_count": 39,
            "medium_confidence_count": 3,
            "low_confidence_count": 0,
            "high_confidence_fields": [
                "credit_report:CreditScore",
                "credit_report:CreditScore_B2",
                "t4:TaxYear",
                "T4_B1:AnnualIncome",
                "T4_B2:AnnualIncome",
            ],
            "medium_confidence_fields": [
                "appraisal:MarketConditions",
                "bank_statement:AvgMonthlyBalance",
                "appraisal:PropertyCondition",
            ],
            "low_confidence_fields": [],
        },
    }


def _marcus_williams_app() -> dict[str, Any]:
    """Insured mortgage — conditional approval."""
    return {
        "id": "app-mw-mtg-001",
        "created_at": "2023-02-18T09:45:00Z",
        "external_reference": "CUST-MW-002",
        "status": "completed",
        "persona": "mortgage_underwriting",
        "files": [],
        "processing_status": "idle",
        "llm_outputs": {
            "application_summary": {
                "borrower_profile": {
                    "section": "application_summary",
                    "subsection": "borrower_profile",
                    "raw": (
                        "Marcus Williams (DOB 1991-11-08) is applying as a sole "
                        "borrower for an insured mortgage to purchase a freehold "
                        "townhouse at 15 Birchwood Terrace, Mississauga, ON L5B "
                        "3K7. Marcus is a Financial Analyst at Meridian Capital "
                        "Group earning $95,000/yr (permanent full-time since "
                        "August 2020). His credit score is 710 (Equifax). He has "
                        "existing debt obligations of $480/mo consisting of a car "
                        "loan ($380/mo, 3 years remaining) and a revolving credit "
                        "card balance ($100/mo minimum). The property is listed at "
                        "$480,000 with an appraised value of $475,000. Marcus is "
                        "putting $48,000 down (10%) sourced from personal savings "
                        "($30,000) and RRSP Home Buyers' Plan withdrawal "
                        "($18,000), resulting in an LTV of 90%. CMHC mortgage "
                        "insurance is required. Banking records at RBC Royal Bank "
                        "show an average monthly balance of $12,800 with an ending "
                        "balance of $35,200 and zero NSF events."
                    ),
                    "parsed": {
                        "borrowers": [
                            {
                                "name": "Marcus Williams",
                                "date_of_birth": "1991-11-08",
                                "SIN": None,
                                "credit_score": 710,
                                "employment": {
                                    "employer": "Meridian Capital Group",
                                    "position": "Financial Analyst",
                                    "status": "Permanent full-time",
                                    "start_date": "2020-08-10",
                                    "annual_base_salary_CAD": 95000,
                                    "other_compensation_CAD": 0,
                                    "total_employment_income_2021_CAD": 95000,
                                    "net_income_2020_CAD": 38000,
                                },
                                "income_sources": [
                                    {
                                        "type": "Employment",
                                        "employer": "Meridian Capital Group",
                                        "annual_income_CAD": 95000,
                                    },
                                ],
                                "existing_debts_and_liabilities": {
                                    "open_revolving_accounts": 1,
                                    "installment_loans": (
                                        "Car loan — $380/mo, 36 months remaining"
                                    ),
                                    "derogatory_items": "None",
                                    "total_monthly_debt_obligations_CAD": 480,
                                },
                            },
                        ],
                        "property": {
                            "address": (
                                "15 Birchwood Terrace, Mississauga, ON L5B 3K7"
                            ),
                            "type": "Freehold townhouse",
                            "occupancy": "Owner-occupied (Primary residence)",
                            "purchase_price_CAD": 480000,
                            "appraised_value_CAD": 475000,
                            "deposit_paid_CAD": 15000,
                            "market_conditions": "Active",
                            "observed_condition": "Good",
                        },
                        "loan": {
                            "requested_mortgage_CAD": 432000,
                            "LTV_percent": 90.0,
                            "rate": "5.24% Fixed",
                            "term_years": 5,
                            "amortization_years": 25,
                            "down_payment_CAD": 48000,
                            "down_payment_sources": [
                                {"type": "Savings", "amount_CAD": 30000},
                                {"type": "RRSP HBP", "amount_CAD": 18000},
                            ],
                            "closing_date": "2023-04-30",
                        },
                        "banking": {
                            "institution": "RBC Royal Bank",
                            "account_masked": "******8834",
                            "avg_monthly_balance_CAD": 12800,
                            "ending_balance_CAD": 35200,
                            "largest_single_deposit_CAD": 5200,
                            "NSF_overdraft_events": 0,
                            "down_payment_funds_observed": True,
                        },
                    },
                },
                "ratio_calculation": {
                    "section": "application_summary",
                    "subsection": "ratio_calculation",
                    "raw": (
                        "Gross Debt Service (GDS) ratio calculated at 36.0%, "
                        "approaching the 39% OSFI B-20 guideline limit. Monthly "
                        "housing costs include mortgage P&I $2,565, property tax "
                        "$375, heating $125, and CMHC insurance premium amortized "
                        "into payment. Total Debt Service (TDS) ratio calculated "
                        "at 42.0%, approaching the 44% limit after including "
                        "$480/mo in existing debt obligations. Gross monthly "
                        "income is $7,917. Stress test at qualifying rate of "
                        "7.24% (contract rate 5.24% + 2.0% buffer) yields a GDS "
                        "of 38.5% and TDS of 44.4%, TDS very close to the 44% "
                        "limit. Ratios are within guidelines but leave minimal "
                        "margin."
                    ),
                    "parsed": {
                        "GDS": 36.0,
                        "TDS": 42.0,
                        "GDS_status": "Acceptable — near limit",
                        "TDS_status": "Acceptable — near limit",
                        "GDS_limit": 39,
                        "TDS_limit": 44,
                    },
                },
                "income_analysis": {
                    "section": "application_summary",
                    "subsection": "income_analysis",
                    "raw": (
                        "Sole borrower gross income of $95,000 per annum. Marcus "
                        "is a permanent full-time Financial Analyst at Meridian "
                        "Capital Group, employed since August 2020 (~2.5 years "
                        "tenure). Prior to this role he was at a different firm "
                        "for 1 year. Income verified through T4 slips (2021, "
                        "2022), recent pay stubs (3 months), and an employment "
                        "letter. The 2020 T4 shows partial-year income of $38,000 "
                        "reflecting mid-year start. Average monthly gross income "
                        "is $7,917. Single-income household with no co-borrower "
                        "support."
                    ),
                    "parsed": {
                        "total_gross_income_CAD": 95000,
                        "avg_monthly_gross_CAD": 7917,
                        "employment_stability": (
                            "Moderate (single income, permanent FT, ~2.5yr tenure)"
                        ),
                        "income_verification": (
                            "Verified via T4s, pay stubs, employment letter"
                        ),
                    },
                },
                "risk_assessment": {
                    "section": "application_summary",
                    "subsection": "risk_assessment",
                    "raw": (
                        "Overall risk profile is MODERATE. Credit risk is moderate "
                        "— credit score of 710 is acceptable but below the 750+ "
                        "preferred threshold; history shows responsible repayment "
                        "patterns. Employment risk is moderate — single income "
                        "with 2.5 years at current employer; loss of employment "
                        "would create immediate affordability pressure. Property "
                        "risk is low — freehold townhouse in an active Mississauga "
                        "market. Debt risk is moderate — car loan and revolving "
                        "credit add $480/mo pushing TDS to 42%. Liquidity risk is "
                        "moderate — ending balance of $35,200 covers down payment "
                        "and estimated closing costs with limited buffer."
                    ),
                    "parsed": {
                        "overall_risk": "Moderate",
                        "credit_risk": "Moderate (credit score 710)",
                        "employment_risk": (
                            "Moderate (single income, 2.5yr tenure)"
                        ),
                        "property_risk": (
                            "Low (freehold townhouse, active market)"
                        ),
                        "debt_risk": (
                            "Moderate (car loan + revolving credit, $480/mo)"
                        ),
                        "liquidity_risk": (
                            "Moderate (limited buffer after down payment)"
                        ),
                    },
                },
                "recommendation": {
                    "section": "application_summary",
                    "subsection": "recommendation",
                    "raw": (
                        "RECOMMENDATION: CONDITIONAL APPROVAL. The application "
                        "meets minimum OSFI B-20 guidelines but with limited "
                        "margin on TDS. Key concerns are the single-income "
                        "exposure and TDS near the 44% limit. Approval is subject "
                        "to: (1) completion of independent employment verification "
                        "directly with Meridian Capital Group, (2) CMHC mortgage "
                        "default insurance approval at the 90% LTV tier, and "
                        "(3) confirmation of RRSP HBP withdrawal of $18,000. "
                        "Recommend close monitoring of any changes in employment "
                        "status or additional debt prior to closing."
                    ),
                    "parsed": {
                        "DECISION": "Conditional Approval",
                        "RATIONALE": (
                            "Meets minimum guidelines but single income and "
                            "near-limit TDS (42%) create moderate risk. "
                            "Acceptable with conditions."
                        ),
                        "CONDITIONS": [
                            (
                                "Independent employment verification with "
                                "Meridian Capital Group"
                            ),
                            "CMHC mortgage default insurance approval (90% LTV)",
                            "Confirmation of RRSP HBP withdrawal ($18,000)",
                        ],
                        "NEXT_STEPS": [
                            "Submit CMHC insurance application",
                            "Contact employer HR for direct verification",
                            "Obtain RRSP HBP withdrawal confirmation from CRA",
                            "Title search and title insurance",
                            "Close by 2023-04-30",
                        ],
                    },
                },
            },
        },
        "extracted_fields": {
            "application:BorrowerName": {
                "field_name": "BorrowerName",
                "value": "Marcus Williams",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:CoBorrowerName": {
                "field_name": "CoBorrowerName",
                "value": None,
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:BorrowerDOB": {
                "field_name": "BorrowerDOB",
                "value": "1991-11-08",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:PurchasePrice": {
                "field_name": "PurchasePrice",
                "value": "480000",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:RequestedLoanAmount": {
                "field_name": "RequestedLoanAmount",
                "value": "432000",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyAddress": {
                "field_name": "PropertyAddress",
                "value": "15 Birchwood Terrace, Mississauga, ON L5B 3K7",
                "confidence": 0.94,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyType": {
                "field_name": "PropertyType",
                "value": "freehold_townhouse",
                "confidence": 0.93,
                "source_file": "mortgage_application.pdf",
            },
            "application:LoanToValueRatio": {
                "field_name": "LoanToValueRatio",
                "value": "90.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyOccupancy": {
                "field_name": "PropertyOccupancy",
                "value": "Owner-occupied",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateTerm": {
                "field_name": "RateTerm",
                "value": "5 years Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:AmortizationYears": {
                "field_name": "AmortizationYears",
                "value": 25,
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ContractRate": {
                "field_name": "ContractRate",
                "value": "5.24%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateType": {
                "field_name": "RateType",
                "value": "Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ClosingDate": {
                "field_name": "ClosingDate",
                "value": "2023-04-30",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentAmount": {
                "field_name": "DownPaymentAmount",
                "value": "48000",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentSource": {
                "field_name": "DownPaymentSource",
                "value": "Savings ($30,000) + RRSP HBP ($18,000)",
                "confidence": 0.91,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentPercent": {
                "field_name": "DownPaymentPercent",
                "value": "10.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:InsuranceRequired": {
                "field_name": "InsuranceRequired",
                "value": "Yes — CMHC",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:InsurancePremium": {
                "field_name": "InsurancePremium",
                "value": "13392",
                "confidence": 0.89,
                "source_file": "mortgage_application.pdf",
            },
            "appraisal:AppraisedValue": {
                "field_name": "AppraisedValue",
                "value": "475000",
                "confidence": 0.95,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:PropertyCondition": {
                "field_name": "PropertyCondition",
                "value": "Good",
                "confidence": 0.92,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:MarketConditions": {
                "field_name": "MarketConditions",
                "value": "Active",
                "confidence": 0.90,
                "source_file": "appraisal_report.pdf",
            },
            "employment_letter:Employer_B1": {
                "field_name": "Employer_B1",
                "value": "Meridian Capital Group",
                "confidence": 0.96,
                "source_file": "employment_letter.pdf",
            },
            "employment_letter:Position_B1": {
                "field_name": "Position_B1",
                "value": "Financial Analyst",
                "confidence": 0.95,
                "source_file": "employment_letter.pdf",
            },
            "employment_letter_B1:BaseSalary": {
                "field_name": "BaseSalary",
                "value": "95000",
                "confidence": 0.96,
                "source_file": "employment_letter.pdf",
            },
            "employment_letter:EmploymentStatus_B1": {
                "field_name": "EmploymentStatus_B1",
                "value": "Permanent full-time",
                "confidence": 0.96,
                "source_file": "employment_letter.pdf",
            },
            "employment_letter:StartDate_B1": {
                "field_name": "StartDate_B1",
                "value": "2020-08-10",
                "confidence": 0.93,
                "source_file": "employment_letter.pdf",
            },
            "T4_B1:AnnualIncome": {
                "field_name": "AnnualIncome",
                "value": "95000",
                "confidence": 0.98,
                "source_file": "t4_2022.pdf",
            },
            "t4:AnnualIncome_2021": {
                "field_name": "AnnualIncome_2021",
                "value": "93500",
                "confidence": 0.98,
                "source_file": "t4_2021.pdf",
            },
            "t4:AnnualIncome_2020": {
                "field_name": "AnnualIncome_2020",
                "value": "38000",
                "confidence": 0.97,
                "source_file": "t4_2020.pdf",
            },
            "bank_statement:DownPaymentSavings": {
                "field_name": "DownPaymentSavings",
                "value": "30000",
                "confidence": 0.92,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:Institution": {
                "field_name": "Institution",
                "value": "RBC Royal Bank",
                "confidence": 0.97,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:EndingBalance": {
                "field_name": "EndingBalance",
                "value": "35200",
                "confidence": 0.94,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:AvgMonthlyBalance": {
                "field_name": "AvgMonthlyBalance",
                "value": "12800",
                "confidence": 0.91,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:NSFEvents": {
                "field_name": "NSFEvents",
                "value": "0",
                "confidence": 0.96,
                "source_file": "bank_statements.pdf",
            },
            "credit_report:CreditScore": {
                "field_name": "CreditScore",
                "value": "710",
                "confidence": 0.99,
                "source_file": "credit_report.pdf",
            },
            "credit_report:RevolvingAccounts": {
                "field_name": "RevolvingAccounts",
                "value": "1",
                "confidence": 0.97,
                "source_file": "credit_report.pdf",
            },
            "credit_report:InstallmentLoans": {
                "field_name": "InstallmentLoans",
                "value": "Car loan — $380/mo, 36 months remaining",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "credit_report:MonthlyDebtObligations": {
                "field_name": "MonthlyDebtObligations",
                "value": "480",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "credit_report:DerogatoryItems": {
                "field_name": "DerogatoryItems",
                "value": "None",
                "confidence": 0.98,
                "source_file": "credit_report.pdf",
            },
            "credit_report:OtherDebtsMonthly": {
                "field_name": "OtherDebtsMonthly",
                "value": "480",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "application:PropertyTaxesAnnual": {
                "field_name": "PropertyTaxesAnnual",
                "value": "4500",
                "confidence": 0.93,
                "source_file": "mortgage_application.pdf",
            },
            "application:HeatingMonthly": {
                "field_name": "HeatingMonthly",
                "value": "125",
                "confidence": 0.92,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmployerName": {
                "field_name": "EmployerName",
                "value": "Meridian Capital Group",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:OccupationTitle": {
                "field_name": "OccupationTitle",
                "value": "Financial Analyst",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmploymentStatus": {
                "field_name": "EmploymentStatus",
                "value": "Permanent full-time",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:QualifyingRate": {
                "field_name": "QualifyingRate",
                "value": "7.24%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "rrsp:HBPWithdrawalAmount": {
                "field_name": "HBPWithdrawalAmount",
                "value": "18000",
                "confidence": 0.90,
                "source_file": "rrsp_statement.pdf",
            },
        },
        "confidence_summary": {
            "total_fields": 48,
            "average_confidence": 0.95,
            "high_confidence_count": 36,
            "medium_confidence_count": 5,
            "low_confidence_count": 0,
            "high_confidence_fields": [
                "credit_report:CreditScore",
                "T4_B1:AnnualIncome",
                "t4:AnnualIncome_2021",
                "application:PurchasePrice",
                "application:RequestedLoanAmount",
            ],
            "medium_confidence_fields": [
                "application:InsurancePremium",
                "rrsp:HBPWithdrawalAmount",
                "appraisal:MarketConditions",
                "bank_statement:AvgMonthlyBalance",
                "application:DownPaymentSource",
            ],
            "low_confidence_fields": [],
        },
    }


def _priya_patel_app() -> dict[str, Any]:
    """High-ratio insured mortgage — declined."""
    return {
        "id": "app-pp-mtg-001",
        "created_at": "2024-01-05T11:20:00Z",
        "external_reference": "CUST-PP-003",
        "status": "completed",
        "persona": "mortgage_underwriting",
        "files": [],
        "processing_status": "idle",
        "llm_outputs": {
            "application_summary": {
                "borrower_profile": {
                    "section": "application_summary",
                    "subsection": "borrower_profile",
                    "raw": (
                        "Priya Patel (DOB 1993-05-20) is applying as a sole "
                        "borrower for a high-ratio insured mortgage to purchase "
                        "a condominium at Unit 2408, 88 Harbour St, Toronto, ON "
                        "M5J 0B5. Priya is a self-employed freelance UX Consultant "
                        "operating as a sole proprietor under the trade name "
                        "'Patel Design Studio' since January 2022 (~2 years of "
                        "self-employment history). She reports gross self-employment "
                        "income of $110,000 for 2023, with 2022 income of $85,000 "
                        "and 2021 income of $52,000 (partial year). Net "
                        "self-employment income after business expenses averaged "
                        "$78,500 over the past two complete tax years. Income is "
                        "variable and project-based with no guaranteed contracts. "
                        "No co-borrower. Credit score is 680 (Equifax). Existing "
                        "debt obligations total $620/mo including a student loan "
                        "($320/mo), a line of credit ($200/mo minimum), and a "
                        "credit card ($100/mo minimum). The property is a "
                        "downtown Toronto condo listed at $750,000 with an "
                        "appraised value of $740,000. Priya is putting $37,500 "
                        "down (5%) from personal savings, resulting in an LTV of "
                        "95%. CMHC mortgage insurance required. Banking records "
                        "at Scotiabank show an average monthly balance of $8,400 "
                        "with an ending balance of $41,200, with 2 NSF events in "
                        "the past 12 months. Monthly income deposits are irregular "
                        "in timing and amount."
                    ),
                    "parsed": {
                        "borrowers": [
                            {
                                "name": "Priya Patel",
                                "date_of_birth": "1993-05-20",
                                "SIN": None,
                                "credit_score": 680,
                                "employment": {
                                    "employer": "Self-employed (Patel Design Studio)",
                                    "position": "Freelance UX Consultant",
                                    "status": "Self-employed — sole proprietor",
                                    "start_date": "2022-01-15",
                                    "annual_base_salary_CAD": 0,
                                    "other_compensation_CAD": 0,
                                    "total_employment_income_2021_CAD": 0,
                                    "net_income_2020_CAD": 0,
                                    "gross_self_employment_income_2023_CAD": 110000,
                                    "gross_self_employment_income_2022_CAD": 85000,
                                    "net_self_employment_income_avg_CAD": 78500,
                                },
                                "income_sources": [
                                    {
                                        "type": "Self-employment",
                                        "employer": "Patel Design Studio",
                                        "annual_income_CAD": 110000,
                                        "income_variability": "High — project-based",
                                    },
                                ],
                                "existing_debts_and_liabilities": {
                                    "open_revolving_accounts": 2,
                                    "installment_loans": (
                                        "Student loan — $320/mo, 84 months remaining"
                                    ),
                                    "derogatory_items": (
                                        "2 NSF events in past 12 months"
                                    ),
                                    "total_monthly_debt_obligations_CAD": 620,
                                },
                            },
                        ],
                        "property": {
                            "address": (
                                "Unit 2408, 88 Harbour St, Toronto, ON M5J 0B5"
                            ),
                            "type": "Condominium",
                            "occupancy": "Owner-occupied (Primary residence)",
                            "purchase_price_CAD": 750000,
                            "appraised_value_CAD": 740000,
                            "deposit_paid_CAD": 10000,
                            "market_conditions": "Cooling",
                            "observed_condition": "Good",
                            "condo_fees_monthly_CAD": 580,
                        },
                        "loan": {
                            "requested_mortgage_CAD": 712500,
                            "LTV_percent": 95.0,
                            "rate": "5.89% Fixed",
                            "term_years": 5,
                            "amortization_years": 25,
                            "down_payment_CAD": 37500,
                            "down_payment_sources": [
                                {"type": "Savings", "amount_CAD": 37500},
                            ],
                            "closing_date": "2024-03-15",
                        },
                        "banking": {
                            "institution": "Scotiabank",
                            "account_masked": "******6217",
                            "avg_monthly_balance_CAD": 8400,
                            "ending_balance_CAD": 41200,
                            "largest_single_deposit_CAD": 18500,
                            "NSF_overdraft_events": 2,
                            "down_payment_funds_observed": True,
                        },
                    },
                },
                "ratio_calculation": {
                    "section": "application_summary",
                    "subsection": "ratio_calculation",
                    "raw": (
                        "Gross Debt Service (GDS) ratio calculated at 41.0%, "
                        "EXCEEDING the 39% OSFI B-20 guideline limit. Monthly "
                        "housing costs include mortgage P&I $4,520, property tax "
                        "$312, heating $83, and condo fees $580 (50% included per "
                        "policy), totaling $5,205. Using the two-year average net "
                        "self-employment income of $78,500, gross monthly income "
                        "is $6,542 (net) or $9,167 (gross reported). Using the "
                        "more conservative net figure: GDS = 5,205 / 6,542 = "
                        "79.6% (fails). Even using gross: GDS = 5,205 / 9,167 = "
                        "56.8% (fails). Using a blended qualifying income of "
                        "$95,000 (2-year average of reported gross): GDS = "
                        "5,205 / 7,917 = 65.8% (fails). NOTE: For presentation "
                        "purposes using the borrower's stated gross of $110,000, "
                        "GDS = 41.0% and TDS = 47.0%, but even these reported "
                        "figures exceed limits. Total Debt Service (TDS) ratio "
                        "at 47.0% using stated gross, EXCEEDING the 44% limit "
                        "after including $620/mo existing debt. Stress test at "
                        "qualifying rate of 7.89% (contract rate 5.89% + 2.0% "
                        "buffer) yields GDS of 50.2% and TDS of 56.8%, both "
                        "significantly exceeding limits. The Minimum Qualifying "
                        "Rate (MQR) of 7.24% (floor) also results in failure: "
                        "GDS 48.1% and TDS 54.5%."
                    ),
                    "parsed": {
                        "GDS": 41.0,
                        "TDS": 47.0,
                        "GDS_status": "Exceeds limit",
                        "TDS_status": "Exceeds limit",
                        "GDS_limit": 39,
                        "TDS_limit": 44,
                        "stress_test_MQR": 7.24,
                        "stress_test_GDS": 48.1,
                        "stress_test_TDS": 54.5,
                        "stress_test_result": "FAIL",
                    },
                },
                "income_analysis": {
                    "section": "application_summary",
                    "subsection": "income_analysis",
                    "raw": (
                        "Sole borrower reports gross self-employment income of "
                        "$110,000 for 2023, $85,000 for 2022, and $52,000 for "
                        "2021 (partial year). Two-year average gross is $97,500. "
                        "Net self-employment income after deducting business "
                        "expenses averaged $78,500 over the two complete tax "
                        "years. Income is derived from freelance UX consulting "
                        "engagements with no long-term contracts or guaranteed "
                        "revenue. T1 General tax returns and Notices of Assessment "
                        "confirm the declared income. Bank deposits show irregular "
                        "patterns with significant month-to-month variability — "
                        "monthly deposits range from $3,200 to $18,500. Only 2 "
                        "years of self-employment history; lender guidelines "
                        "typically require minimum 2–3 years. No co-borrower "
                        "income to supplement. Overall income stability is WEAK."
                    ),
                    "parsed": {
                        "total_gross_income_CAD": 110000,
                        "avg_monthly_gross_CAD": 9167,
                        "employment_stability": (
                            "Weak (self-employed, variable income, 2yr history)"
                        ),
                        "income_verification": (
                            "T1 General returns, NOAs, bank deposit analysis"
                        ),
                        "self_employment_details": {
                            "years_self_employed": 2,
                            "gross_2023": 110000,
                            "gross_2022": 85000,
                            "gross_2021_partial": 52000,
                            "net_avg_2yr": 78500,
                            "income_trend": "Increasing but short history",
                        },
                    },
                },
                "risk_assessment": {
                    "section": "application_summary",
                    "subsection": "risk_assessment",
                    "raw": (
                        "Overall risk profile is HIGH. Credit risk is elevated — "
                        "credit score of 680 is at the minimum acceptable "
                        "threshold with 2 NSF events in the past 12 months "
                        "indicating cash-flow management issues. Employment risk "
                        "is high — self-employed with only 2 years of history, "
                        "variable project-based income, and no co-borrower; "
                        "lender guidelines typically require 2–3 years minimum "
                        "for self-employed borrowers. Property risk is moderate — "
                        "downtown Toronto condo in a cooling market; high condo "
                        "fees ($580/mo) impact affordability; appraised value "
                        "($740,000) is below purchase price ($750,000). Debt risk "
                        "is high — existing debt of $620/mo combined with an "
                        "aggressive LTV of 95% results in TDS well above the 44% "
                        "limit. Liquidity risk is elevated — down payment of "
                        "$37,500 leaves minimal reserves after closing costs, and "
                        "irregular income creates cash-flow vulnerability. Stress "
                        "test failure at MQR 7.24% is a disqualifying factor."
                    ),
                    "parsed": {
                        "overall_risk": "High",
                        "credit_risk": (
                            "Elevated (credit score 680, 2 NSF events)"
                        ),
                        "employment_risk": (
                            "High (self-employed, 2yr history, variable income)"
                        ),
                        "property_risk": (
                            "Moderate (condo, cooling market, appraisal gap)"
                        ),
                        "debt_risk": (
                            "High (TDS 47%, student loan + LOC + credit card)"
                        ),
                        "liquidity_risk": (
                            "Elevated (minimal reserves, irregular income)"
                        ),
                    },
                },
                "recommendation": {
                    "section": "application_summary",
                    "subsection": "recommendation",
                    "raw": (
                        "RECOMMENDATION: DECLINE. This application fails to meet "
                        "OSFI B-20 guidelines on multiple fronts. (1) GDS of 41% "
                        "exceeds the 39% limit. (2) TDS of 47% exceeds the 44% "
                        "limit. (3) Stress test at the Minimum Qualifying Rate "
                        "(MQR) of 7.24% results in GDS of 48.1% and TDS of 54.5%, "
                        "both significantly exceeding limits. (4) Self-employment "
                        "income history of only 2 years with high variability does "
                        "not meet the standard 2–3 year minimum for reliable "
                        "income assessment. (5) Credit score of 680 with recent "
                        "NSF events raises cash-flow management concerns. "
                        "(6) Appraisal gap — property appraised at $740,000 vs "
                        "purchase price of $750,000. The applicant may wish to "
                        "consider: increasing the down payment to reduce LTV and "
                        "ratios, paying down existing debts, building additional "
                        "self-employment track record (3+ years), or adding a "
                        "co-borrower with stable income."
                    ),
                    "parsed": {
                        "DECISION": "Decline",
                        "RATIONALE": (
                            "GDS (41%) and TDS (47%) exceed OSFI B-20 limits. "
                            "Stress test at MQR 7.24% fails with GDS 48.1% and "
                            "TDS 54.5%. Insufficient self-employment history "
                            "(2 years, variable). Credit score 680 with NSF "
                            "events. Appraisal below purchase price."
                        ),
                        "CONDITIONS": [],
                        "NEXT_STEPS": [
                            (
                                "Notify applicant of decline with reasons under "
                                "OSFI B-20"
                            ),
                            (
                                "Advise applicant to increase down payment, pay "
                                "down debts, or add co-borrower"
                            ),
                            (
                                "Applicant may reapply after 3+ years of "
                                "self-employment history"
                            ),
                            "Retain file per regulatory retention requirements",
                        ],
                    },
                },
            },
        },
        "extracted_fields": {
            "application:BorrowerName": {
                "field_name": "BorrowerName",
                "value": "Priya Patel",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:CoBorrowerName": {
                "field_name": "CoBorrowerName",
                "value": None,
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:BorrowerDOB": {
                "field_name": "BorrowerDOB",
                "value": "1993-05-20",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:PurchasePrice": {
                "field_name": "PurchasePrice",
                "value": "750000",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:RequestedLoanAmount": {
                "field_name": "RequestedLoanAmount",
                "value": "712500",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyAddress": {
                "field_name": "PropertyAddress",
                "value": "Unit 2408, 88 Harbour St, Toronto, ON M5J 0B5",
                "confidence": 0.94,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyType": {
                "field_name": "PropertyType",
                "value": "condominium",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:LoanToValueRatio": {
                "field_name": "LoanToValueRatio",
                "value": "95.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:PropertyOccupancy": {
                "field_name": "PropertyOccupancy",
                "value": "Owner-occupied",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateTerm": {
                "field_name": "RateTerm",
                "value": "5 years Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:AmortizationYears": {
                "field_name": "AmortizationYears",
                "value": 25,
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ContractRate": {
                "field_name": "ContractRate",
                "value": "5.89%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:RateType": {
                "field_name": "RateType",
                "value": "Fixed",
                "confidence": 0.98,
                "source_file": "mortgage_application.pdf",
            },
            "application:ClosingDate": {
                "field_name": "ClosingDate",
                "value": "2024-03-15",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentAmount": {
                "field_name": "DownPaymentAmount",
                "value": "37500",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentSource": {
                "field_name": "DownPaymentSource",
                "value": "Personal savings",
                "confidence": 0.92,
                "source_file": "mortgage_application.pdf",
            },
            "application:DownPaymentPercent": {
                "field_name": "DownPaymentPercent",
                "value": "5.0%",
                "confidence": 0.96,
                "source_file": "mortgage_application.pdf",
            },
            "application:InsuranceRequired": {
                "field_name": "InsuranceRequired",
                "value": "Yes — CMHC",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
            "application:InsurancePremium": {
                "field_name": "InsurancePremium",
                "value": "28500",
                "confidence": 0.88,
                "source_file": "mortgage_application.pdf",
            },
            "application:CondoFeesMonthly": {
                "field_name": "CondoFeesMonthly",
                "value": "580",
                "confidence": 0.94,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmploymentStatus": {
                "field_name": "EmploymentStatus",
                "value": "Self-employed — sole proprietor",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "appraisal:AppraisedValue": {
                "field_name": "AppraisedValue",
                "value": "740000",
                "confidence": 0.95,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:PropertyCondition": {
                "field_name": "PropertyCondition",
                "value": "Good",
                "confidence": 0.91,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:MarketConditions": {
                "field_name": "MarketConditions",
                "value": "Cooling",
                "confidence": 0.88,
                "source_file": "appraisal_report.pdf",
            },
            "appraisal:AppraisalGap": {
                "field_name": "AppraisalGap",
                "value": "-10000",
                "confidence": 0.93,
                "source_file": "appraisal_report.pdf",
            },
            "t1_general:GrossIncome_2023": {
                "field_name": "GrossIncome_2023",
                "value": "110000",
                "confidence": 0.96,
                "source_file": "t1_general_2023.pdf",
            },
            "t1_general:GrossIncome_2022": {
                "field_name": "GrossIncome_2022",
                "value": "85000",
                "confidence": 0.96,
                "source_file": "t1_general_2022.pdf",
            },
            "t1_general:NetIncome_2023": {
                "field_name": "NetIncome_2023",
                "value": "82000",
                "confidence": 0.94,
                "source_file": "t1_general_2023.pdf",
            },
            "t1_general:NetIncome_2022": {
                "field_name": "NetIncome_2022",
                "value": "75000",
                "confidence": 0.94,
                "source_file": "t1_general_2022.pdf",
            },
            "t1_general:BusinessExpenses_2023": {
                "field_name": "BusinessExpenses_2023",
                "value": "28000",
                "confidence": 0.91,
                "source_file": "t1_general_2023.pdf",
            },
            "T4_B1:AnnualIncome": {
                "field_name": "AnnualIncome",
                "value": "110000",
                "confidence": 0.96,
                "source_file": "t1_general_2023.pdf",
            },
            "noa:AssessedIncome_2022": {
                "field_name": "AssessedIncome_2022",
                "value": "85000",
                "confidence": 0.97,
                "source_file": "noa_2022.pdf",
            },
            "noa:AssessedIncome_2023": {
                "field_name": "AssessedIncome_2023",
                "value": "110000",
                "confidence": 0.97,
                "source_file": "noa_2023.pdf",
            },
            "bank_statement:DownPaymentAmount": {
                "field_name": "DownPaymentAmount",
                "value": "37500",
                "confidence": 0.91,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:Institution": {
                "field_name": "Institution",
                "value": "Scotiabank",
                "confidence": 0.97,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:EndingBalance": {
                "field_name": "EndingBalance",
                "value": "41200",
                "confidence": 0.93,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:AvgMonthlyBalance": {
                "field_name": "AvgMonthlyBalance",
                "value": "8400",
                "confidence": 0.90,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:NSFEvents": {
                "field_name": "NSFEvents",
                "value": "2",
                "confidence": 0.96,
                "source_file": "bank_statements.pdf",
            },
            "bank_statement:IncomeRegularity": {
                "field_name": "IncomeRegularity",
                "value": "Irregular — deposits range $3,200 to $18,500",
                "confidence": 0.87,
                "source_file": "bank_statements.pdf",
            },
            "credit_report:CreditScore": {
                "field_name": "CreditScore",
                "value": "680",
                "confidence": 0.99,
                "source_file": "credit_report.pdf",
            },
            "credit_report:RevolvingAccounts": {
                "field_name": "RevolvingAccounts",
                "value": "2",
                "confidence": 0.97,
                "source_file": "credit_report.pdf",
            },
            "credit_report:InstallmentLoans": {
                "field_name": "InstallmentLoans",
                "value": "Student loan — $320/mo, 84 months remaining",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "credit_report:MonthlyDebtObligations": {
                "field_name": "MonthlyDebtObligations",
                "value": "620",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "credit_report:DerogatoryItems": {
                "field_name": "DerogatoryItems",
                "value": "2 NSF events (past 12 months)",
                "confidence": 0.96,
                "source_file": "credit_report.pdf",
            },
            "credit_report:OtherDebtsMonthly": {
                "field_name": "OtherDebtsMonthly",
                "value": "620",
                "confidence": 0.95,
                "source_file": "credit_report.pdf",
            },
            "application:PropertyTaxesAnnual": {
                "field_name": "PropertyTaxesAnnual",
                "value": "3750",
                "confidence": 0.93,
                "source_file": "mortgage_application.pdf",
            },
            "application:HeatingMonthly": {
                "field_name": "HeatingMonthly",
                "value": "83",
                "confidence": 0.92,
                "source_file": "mortgage_application.pdf",
            },
            "application:EmployerName": {
                "field_name": "EmployerName",
                "value": "Patel Design Studio",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:OccupationTitle": {
                "field_name": "OccupationTitle",
                "value": "Freelance UX Consultant",
                "confidence": 0.95,
                "source_file": "mortgage_application.pdf",
            },
            "application:QualifyingRate": {
                "field_name": "QualifyingRate",
                "value": "7.89%",
                "confidence": 0.97,
                "source_file": "mortgage_application.pdf",
            },
        },
        "confidence_summary": {
            "total_fields": 50,
            "average_confidence": 0.94,
            "high_confidence_count": 35,
            "medium_confidence_count": 7,
            "low_confidence_count": 1,
            "high_confidence_fields": [
                "credit_report:CreditScore",
                "noa:AssessedIncome_2023",
                "noa:AssessedIncome_2022",
                "application:PurchasePrice",
                "application:RequestedLoanAmount",
            ],
            "medium_confidence_fields": [
                "bank_statement:AvgMonthlyBalance",
                "bank_statement:IncomeRegularity",
                "appraisal:MarketConditions",
                "application:InsurancePremium",
                "t1_general:BusinessExpenses_2023",
                "appraisal:PropertyCondition",
                "bank_statement:DownPaymentAmount",
            ],
            "low_confidence_fields": [
                "bank_statement:IncomeRegularity",
            ],
        },
    }


def get_mortgage_apps() -> list[dict[str, Any]]:
    """Return seed data for 3 mortgage underwriting applications.

    Each dict is suitable for constructing an ``ApplicationMetadata`` object.
    """
    return [
        _sarah_chen_app(),
        _marcus_williams_app(),
        _priya_patel_app(),
    ]
