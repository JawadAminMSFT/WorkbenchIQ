#!/usr/bin/env python3
"""
Setup script for Mortgage Underwriting Custom Analyzer.

Creates and deploys the custom Azure Content Understanding analyzer for:
- mortgageDocAnalyzer: Document extraction for Canadian mortgage documents
  (T4, pay stubs, employment letters, NOA, appraisals, bank statements, etc.)

Usage:
    python scripts/setup_mortgage_analyzers.py [--verify] [--delete]
    
Options:
    --verify    Only verify analyzer exists, don't create/update
    --delete    Delete the mortgage analyzer
    --force     Force recreate even if analyzer exists
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Analyzer Schema Definitions
# =============================================================================

# Mortgage Document Analyzer Schema - for all mortgage document types
MORTGAGE_DOC_FIELD_SCHEMA = {
    "name": "MortgageDocFields",
    "description": "Field schema for Canadian mortgage document extraction",
    "fields": {
        # ===== Borrower Identity =====
        "BorrowerFullName": {
            "type": "string",
            "method": "extract",
            "description": "Full legal name of the primary mortgage borrower",
        },
        "BorrowerDateOfBirth": {
            "type": "date",
            "method": "extract",
            "description": "Borrower's date of birth",
        },
        "BorrowerSIN": {
            "type": "string",
            "method": "extract",
            "description": "Social Insurance Number (Canadian: XXX-XXX-XXX format)",
        },
        "BorrowerAddress": {
            "type": "string",
            "method": "extract",
            "description": "Current residential address of borrower",
        },
        "CoBorrowerName": {
            "type": "string",
            "method": "extract",
            "description": "Full name of co-borrower/co-applicant if present",
        },
        
        # ===== Employment Information =====
        "EmployerName": {
            "type": "string",
            "method": "extract",
            "description": "Name of employer or business",
        },
        "EmployerAddress": {
            "type": "string",
            "method": "extract",
            "description": "Employer's business address",
        },
        "PositionTitle": {
            "type": "string",
            "method": "extract",
            "description": "Job title or position",
        },
        "EmploymentStartDate": {
            "type": "date",
            "method": "extract",
            "description": "Date employment commenced",
        },
        "EmploymentType": {
            "type": "string",
            "method": "extract",
            "description": "Employment type: Full-time, Part-time, Contract, Self-employed",
        },
        "EmploymentStatus": {
            "type": "string",
            "method": "extract",
            "description": "Status: Permanent, Probationary, Temporary, Contract",
        },
        
        # ===== Income - Pay Stub Fields =====
        "PayPeriod": {
            "type": "string",
            "method": "extract",
            "description": "Pay period dates (e.g., Jan 1 - Jan 15, 2026)",
        },
        "PayDate": {
            "type": "date",
            "method": "extract",
            "description": "Date of payment on pay stub",
        },
        "GrossPayPeriodAmount": {
            "type": "number",
            "method": "extract",
            "description": "Gross earnings for the pay period in CAD",
        },
        "NetPayPeriodAmount": {
            "type": "number",
            "method": "extract",
            "description": "Net (take-home) pay for the period in CAD",
        },
        "YTDEarnings": {
            "type": "number",
            "method": "extract",
            "description": "Year-to-date gross earnings in CAD",
        },
        "YTDGrossEarnings": {
            "type": "number",
            "method": "extract",
            "description": "Year-to-date gross earnings in CAD (alias for YTDEarnings)",
        },
        "YTDNetEarnings": {
            "type": "number",
            "method": "extract",
            "description": "Year-to-date net earnings in CAD",
        },
        "RegularHours": {
            "type": "number",
            "method": "extract",
            "description": "Regular hours worked in pay period",
        },
        "OvertimeHours": {
            "type": "number",
            "method": "extract",
            "description": "Overtime hours worked in pay period",
        },
        "HourlyRate": {
            "type": "number",
            "method": "extract",
            "description": "Hourly wage rate if applicable",
        },
        
        # ===== Income - Annual/Salary Fields =====
        "GrossAnnualSalary": {
            "type": "number",
            "method": "extract",
            "description": "Gross annual salary or wages in CAD",
        },
        "BonusAmount": {
            "type": "number",
            "method": "extract",
            "description": "Annual bonus amount in CAD",
        },
        "CommissionAmount": {
            "type": "number",
            "method": "extract",
            "description": "Annual commission income in CAD",
        },
        "OvertimeAnnual": {
            "type": "number",
            "method": "extract",
            "description": "Annual overtime earnings in CAD",
        },
        
        # ===== T4 Specific Fields =====
        "TaxYear": {
            "type": "integer",
            "method": "extract",
            "description": "Tax year for T4 or NOA document",
        },
        "TotalIncomeFromT4": {
            "type": "number",
            "method": "extract",
            "description": "Box 14 - Total employment income from T4",
        },
        "IncomeTaxDeducted": {
            "type": "number",
            "method": "extract",
            "description": "Box 22 - Income tax deducted on T4",
        },
        "CPPContributions": {
            "type": "number",
            "method": "extract",
            "description": "Box 16 - CPP contributions on T4",
        },
        "EIInsurablePremiums": {
            "type": "number",
            "method": "extract",
            "description": "Box 18 - EI premiums on T4",
        },
        "RPPContributions": {
            "type": "number",
            "method": "extract",
            "description": "Box 20 - RPP contributions on T4",
        },
        
        # ===== NOA Specific Fields =====
        "TotalIncomeFromNOA": {
            "type": "number",
            "method": "extract",
            "description": "Line 15000 - Total income from Notice of Assessment",
        },
        "NetIncomeFromNOA": {
            "type": "number",
            "method": "extract",
            "description": "Line 23600 - Net income from NOA",
        },
        "TaxableIncomeFromNOA": {
            "type": "number",
            "method": "extract",
            "description": "Line 26000 - Taxable income from NOA",
        },
        "TaxOwedOrRefund": {
            "type": "number",
            "method": "extract",
            "description": "Balance owing or refund amount from NOA",
        },
        "RRSPDeductionLimit": {
            "type": "number",
            "method": "extract",
            "description": "RRSP deduction limit for next year from NOA",
        },
        
        # ===== Credit Report Fields =====
        "CreditScore": {
            "type": "integer",
            "method": "extract",
            "description": "Credit score (Equifax or TransUnion, range 300-900)",
        },
        "CreditBureau": {
            "type": "string",
            "method": "extract",
            "description": "Credit bureau: Equifax or TransUnion",
        },
        "CreditReportDate": {
            "type": "date",
            "method": "extract",
            "description": "Date the credit report was pulled",
        },
        
        # ===== Property Information =====
        "PropertyAddress": {
            "type": "string",
            "method": "extract",
            "description": "Full civic address of subject property",
        },
        "PropertyType": {
            "type": "string",
            "method": "extract",
            "description": "Property type: Detached, Semi, Townhouse, Condo, etc.",
        },
        "PurchasePrice": {
            "type": "number",
            "method": "extract",
            "description": "Purchase price from agreement of purchase and sale",
        },
        "AppraisedValue": {
            "type": "number",
            "method": "extract",
            "description": "Appraised market value from appraisal report",
        },
        "PropertyTaxesAnnual": {
            "type": "number",
            "method": "extract",
            "description": "Annual property taxes in CAD",
        },
        "CondoFeesMonthly": {
            "type": "number",
            "method": "extract",
            "description": "Monthly condominium fees if applicable",
        },
        "HeatingCostMonthly": {
            "type": "number",
            "method": "extract",
            "description": "Estimated monthly heating costs",
        },
        "LotSize": {
            "type": "string",
            "method": "extract",
            "description": "Lot dimensions or area",
        },
        "YearBuilt": {
            "type": "integer",
            "method": "extract",
            "description": "Year the property was built",
        },
        "LivingArea": {
            "type": "number",
            "method": "extract",
            "description": "Living area in square feet",
        },
        
        # ===== Appraisal Specific Fields =====
        "AppraisalDate": {
            "type": "date",
            "method": "extract",
            "description": "Date of property appraisal",
        },
        "AppraiserName": {
            "type": "string",
            "method": "extract",
            "description": "Name of the certified appraiser",
        },
        "AppraiserLicense": {
            "type": "string",
            "method": "extract",
            "description": "Appraiser license/designation number",
        },
        "ComparableSales": {
            "type": "array",
            "method": "extract",
            "description": "Comparable property sales used for valuation",
            "items": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "salePrice": {"type": "number"},
                    "saleDate": {"type": "date"},
                    "adjustment": {"type": "number"},
                },
            },
        },
        
        # ===== Loan Details =====
        "RequestedLoanAmount": {
            "type": "number",
            "method": "extract",
            "description": "Requested mortgage principal amount in CAD",
        },
        "DownPaymentAmount": {
            "type": "number",
            "method": "extract",
            "description": "Down payment amount in CAD",
        },
        "DownPaymentPercentage": {
            "type": "number",
            "method": "extract",
            "description": "Down payment as percentage of purchase price",
        },
        "RequestedAmortization": {
            "type": "integer",
            "method": "extract",
            "description": "Requested amortization period in years",
        },
        "InterestRate": {
            "type": "number",
            "method": "extract",
            "description": "Mortgage interest rate as percentage",
        },
        "RateTerm": {
            "type": "string",
            "method": "extract",
            "description": "Interest rate term: Variable, 1-year, 5-year fixed, etc.",
        },
        "PaymentFrequency": {
            "type": "string",
            "method": "extract",
            "description": "Payment frequency: Monthly, Bi-weekly, Accelerated bi-weekly",
        },
        "MortgagePaymentAmount": {
            "type": "number",
            "method": "extract",
            "description": "Regular mortgage payment amount",
        },
        
        # ===== Gift Letter Fields =====
        "GiftDonorName": {
            "type": "string",
            "method": "extract",
            "description": "Name of the gift donor",
        },
        "GiftAmount": {
            "type": "number",
            "method": "extract",
            "description": "Amount of the gift in CAD",
        },
        "GiftRelationship": {
            "type": "string",
            "method": "extract",
            "description": "Relationship of donor to borrower: Parent, Sibling, etc.",
        },
        "GiftRepaymentRequired": {
            "type": "boolean",
            "method": "extract",
            "description": "Whether repayment is required (should be false for true gift)",
        },
        "GiftLetterDate": {
            "type": "date",
            "method": "extract",
            "description": "Date of the signed gift letter",
        },
        
        # ===== Bank Statement Fields =====
        "BankName": {
            "type": "string",
            "method": "extract",
            "description": "Name of financial institution",
        },
        "AccountNumber": {
            "type": "string",
            "method": "extract",
            "description": "Bank account number (may be partially masked)",
        },
        "AccountType": {
            "type": "string",
            "method": "extract",
            "description": "Account type: Chequing, Savings, TFSA, RRSP",
        },
        "StatementPeriod": {
            "type": "string",
            "method": "extract",
            "description": "Statement period dates",
        },
        "OpeningBalance": {
            "type": "number",
            "method": "extract",
            "description": "Opening balance for statement period",
        },
        "ClosingBalance": {
            "type": "number",
            "method": "extract",
            "description": "Closing balance for statement period",
        },
        "LargeDeposits": {
            "type": "array",
            "method": "extract",
            "description": "Large deposits requiring source verification",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "date"},
                    "amount": {"type": "number"},
                    "description": {"type": "string"},
                },
            },
        },
        
        # ===== Liabilities =====
        "MonthlyDebtPayments": {
            "type": "number",
            "method": "extract",
            "description": "Total monthly debt obligations (car, credit cards, etc.)",
        },
        "CreditCardBalances": {
            "type": "number",
            "method": "extract",
            "description": "Total outstanding credit card balances",
        },
        "AutoLoanBalance": {
            "type": "number",
            "method": "extract",
            "description": "Outstanding auto loan balance",
        },
        "AutoLoanPayment": {
            "type": "number",
            "method": "extract",
            "description": "Monthly auto loan payment",
        },
        "StudentLoanBalance": {
            "type": "number",
            "method": "extract",
            "description": "Outstanding student loan balance",
        },
        "OtherMortgages": {
            "type": "number",
            "method": "extract",
            "description": "Monthly payments on other mortgages",
        },
        
        # ===== Document Metadata =====
        "DocumentDate": {
            "type": "date",
            "method": "extract",
            "description": "Date on the document",
        },
        "DocumentType": {
            "type": "string",
            "method": "generate",
            "description": "Detected document type: T4, PayStub, EmploymentLetter, NOA, Appraisal, BankStatement, GiftLetter, PurchaseAgreement, CreditReport",
        },
    },
}

# Full analyzer definition with configuration
MORTGAGE_DOC_ANALYZER_SCHEMA = {
    "analyzerId": "mortgageDocAnalyzer",
    "description": "Canadian mortgage document analyzer for T4s, pay stubs, employment letters, NOAs, appraisals, bank statements, gift letters, and credit reports",
    "baseAnalyzerId": "prebuilt-document",
    "fieldSchema": MORTGAGE_DOC_FIELD_SCHEMA,
    "config": {
        "returnDetails": True,
        "enableOcr": True,
        "enableLayout": True,
        "tableFormat": "markdown",
        "estimateFieldSourceAndConfidence": True,
    },
    "models": {
        "completion": "gpt-4.1",
    },
}

# Analyzer configurations dict (matches automotive pattern)
ANALYZER_CONFIGS = {
    "mortgageDocAnalyzer": {
        "description": MORTGAGE_DOC_ANALYZER_SCHEMA["description"],
        "baseAnalyzerId": MORTGAGE_DOC_ANALYZER_SCHEMA["baseAnalyzerId"],
        "fieldSchema": MORTGAGE_DOC_ANALYZER_SCHEMA["fieldSchema"],
        "config": MORTGAGE_DOC_ANALYZER_SCHEMA["config"],
        "models": MORTGAGE_DOC_ANALYZER_SCHEMA["models"],
    },
}


# =============================================================================
# Azure Content Understanding API Functions
# =============================================================================

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for Azure CU API."""
    use_azure_ad = os.getenv("AZURE_CONTENT_UNDERSTANDING_USE_AZURE_AD", "true").lower() == "true"
    api_key = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY")
    
    headers = {"x-ms-useragent": "mortgage-underwriting-setup"}
    
    if use_azure_ad:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
        except ImportError:
            raise RuntimeError("azure-identity not installed. Run: uv add azure-identity")
        except Exception as e:
            raise RuntimeError(f"Failed to get Azure AD token: {e}. Run: az login")
    elif api_key:
        headers["Ocp-Apim-Subscription-Key"] = api_key
    else:
        raise RuntimeError("No authentication configured. Set AZURE_CONTENT_UNDERSTANDING_API_KEY or use Azure AD.")
    
    return headers


def get_analyzer(analyzer_id: str) -> Optional[Dict[str, Any]]:
    """Check if an analyzer exists and get its configuration."""
    import requests
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    
    if not endpoint:
        raise RuntimeError("AZURE_CONTENT_UNDERSTANDING_ENDPOINT not set")
    
    headers = get_auth_headers()
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if "404" in str(e):
            return None
        raise


def poll_operation(response, headers: Dict[str, str], timeout: int = 120) -> Dict[str, Any]:
    """Poll an async operation until completion."""
    import requests
    
    operation_url = response.headers.get("Operation-Location")
    if not operation_url:
        return {"status": "succeeded"}
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = requests.get(operation_url, headers=headers, timeout=30)
        result.raise_for_status()
        data = result.json()
        
        status = data.get("status", "").lower()
        if status == "succeeded":
            return data.get("result", data)
        elif status == "failed":
            raise RuntimeError(f"Operation failed: {data.get('error', 'Unknown error')}")
        
        time.sleep(2)
    
    raise RuntimeError(f"Operation timed out after {timeout} seconds")


def create_analyzer(analyzer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new custom analyzer."""
    import requests
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    
    headers = get_auth_headers()
    headers["Content-Type"] = "application/json"
    
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}
    
    body = {
        "analyzerId": analyzer_id,
        **config,
    }
    
    response = requests.put(url, headers=headers, params=params, json=body, timeout=60)
    response.raise_for_status()
    
    # Handle async operation
    if response.status_code == 202:
        return poll_operation(response, headers)
    
    return response.json() if response.text else {"analyzerId": analyzer_id, "status": "succeeded"}


def update_analyzer(analyzer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing analyzer (delete and recreate)."""
    delete_analyzer(analyzer_id)
    time.sleep(2)  # Wait for deletion to propagate
    return create_analyzer(analyzer_id, config)


def delete_analyzer(analyzer_id: str) -> bool:
    """Delete an analyzer."""
    import requests
    
    endpoint = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT", "").rstrip("/")
    api_version = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_VERSION", "2025-11-01")
    
    headers = get_auth_headers()
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}"
    params = {"api-version": api_version}
    
    response = requests.delete(url, headers=headers, params=params, timeout=30)
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


def verify_analyzer(analyzer_id: str) -> bool:
    """Verify an analyzer exists and is ready."""
    analyzer = get_analyzer(analyzer_id)
    if analyzer:
        print(f"  ✓ {analyzer_id}: Ready")
        print(f"    Base: {analyzer.get('baseAnalyzerId', 'unknown')}")
        fields = analyzer.get("fieldSchema", {}).get("fields", {})
        print(f"    Fields: {len(fields)} defined")
        return True
    else:
        print(f"  ✗ {analyzer_id}: Not found")
        return False


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Setup mortgage underwriting custom analyzer in Azure Content Understanding"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify analyzer exists, don't create/update",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the mortgage analyzer",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate even if analyzer exists",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output analyzer schema as JSON",
    )
    
    args = parser.parse_args()
    
    # Output JSON schema if requested
    if args.json:
        print(json.dumps(MORTGAGE_DOC_ANALYZER_SCHEMA, indent=2))
        return
    
    print("\n" + "=" * 60)
    print("  Mortgage Underwriting Analyzer Setup")
    print("  Feature: 008-mortgage-underwriting")
    print("=" * 60 + "\n")
    
    # Verify mode
    if args.verify:
        print("Verifying mortgage analyzer...\n")
        success = verify_analyzer("mortgageDocAnalyzer")
        sys.exit(0 if success else 1)
    
    # Delete mode
    if args.delete:
        print("Deleting mortgage analyzer...\n")
        if delete_analyzer("mortgageDocAnalyzer"):
            print("  ✓ mortgageDocAnalyzer deleted")
        else:
            print("  - mortgageDocAnalyzer not found (already deleted)")
        return
    
    # Create/Update mode
    print("Setting up mortgage document analyzer...\n")
    
    analyzer_id = "mortgageDocAnalyzer"
    config = ANALYZER_CONFIGS[analyzer_id]
    
    existing = get_analyzer(analyzer_id)
    
    if existing and not args.force:
        print(f"  ℹ {analyzer_id} already exists")
        print(f"    Use --force to recreate")
        verify_analyzer(analyzer_id)
    else:
        if existing:
            print(f"  Updating {analyzer_id}...")
            result = update_analyzer(analyzer_id, config)
        else:
            print(f"  Creating {analyzer_id}...")
            result = create_analyzer(analyzer_id, config)
        
        print(f"  ✓ {analyzer_id} ready")
        print(f"    Fields: {len(config['fieldSchema']['fields'])}")
    
    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
