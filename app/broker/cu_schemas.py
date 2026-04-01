"""
Field schemas for Commercial Brokerage Content Understanding analyzers.

Defines extraction schemas for:
- Carrier insurance quote documents
- ACORD 125/140 submission documents (SOV, loss runs, prior declarations)
- AM Best credit reports and carrier financial research documents
"""

# =============================================================================
# Quote Document Field Schema
# =============================================================================

BROKER_QUOTE_FIELD_SCHEMA = {
    "name": "BrokerQuoteFields",
    "description": "Extract structured quote fields from carrier insurance quote documents",
    "fields": {
        "CarrierName": {
            "type": "string",
            "method": "extract",
            "description": "Name of the insurance carrier",
        },
        "QuoteReferenceNumber": {
            "type": "string",
            "method": "extract",
            "description": "Quote or proposal reference number",
        },
        "QuoteDate": {
            "type": "date",
            "method": "extract",
            "description": "Date the quote was issued",
        },
        "EffectiveDate": {
            "type": "date",
            "method": "extract",
            "description": "Policy effective/start date",
        },
        "ExpirationDate": {
            "type": "date",
            "method": "extract",
            "description": "Policy expiration/end date",
        },
        "AnnualPremium": {
            "type": "string",
            "method": "extract",
            "description": "Total annual premium amount including all components",
        },
        "TotalInsuredValue": {
            "type": "string",
            "method": "extract",
            "description": "Total insured value (TIV) for all covered property",
        },
        "BuildingLimit": {
            "type": "string",
            "method": "extract",
            "description": "Building coverage limit (replacement cost)",
        },
        "ContentsLimit": {
            "type": "string",
            "method": "extract",
            "description": "Business personal property / contents coverage limit",
        },
        "BusinessInterruptionLimit": {
            "type": "string",
            "method": "extract",
            "description": "Business income / loss of rents coverage limit",
        },
        "Deductibles": {
            "type": "array",
            "method": "extract",
            "description": "List of deductibles by peril type",
            "items": {"type": "string"},
        },
        "FloodSublimit": {
            "type": "string",
            "method": "extract",
            "description": "Flood coverage sublimit",
        },
        "EarthquakeSublimit": {
            "type": "string",
            "method": "extract",
            "description": "Earthquake coverage sublimit or EXCLUDED",
        },
        "NamedPerilsExclusions": {
            "type": "array",
            "method": "extract",
            "description": "Named perils or coverages that are excluded",
            "items": {"type": "string"},
        },
        "SpecialConditions": {
            "type": "array",
            "method": "extract",
            "description": "Special conditions, endorsements, or requirements",
            "items": {"type": "string"},
        },
        "PolicyPeriod": {
            "type": "string",
            "method": "extract",
            "description": "Full policy period (e.g. May 1, 2026 - May 1, 2027)",
        },
        "CarrierAMBestRating": {
            "type": "string",
            "method": "extract",
            "description": "Carrier AM Best financial strength rating",
        },
        "Underwriter": {
            "type": "string",
            "method": "extract",
            "description": "Name and title of the underwriter",
        },
        "CoverageForm": {
            "type": "string",
            "method": "extract",
            "description": "Coverage form (e.g. ISO CP 10 30 Special Form)",
        },
        "ValuationBasis": {
            "type": "string",
            "method": "extract",
            "description": "Valuation method (Replacement Cost, ACV, etc.)",
        },
        "CoinsuranceRequirement": {
            "type": "string",
            "method": "extract",
            "description": "Coinsurance percentage requirement",
        },
        "PremiumBreakdown": {
            "type": "array",
            "method": "extract",
            "description": "Itemized premium breakdown by coverage line",
            "items": {
                "type": "object",
                "properties": {
                    "CoverageLine": {
                        "type": "string",
                        "description": "Coverage component name",
                    },
                    "Premium": {
                        "type": "string",
                        "description": "Annual premium for this component",
                    },
                },
            },
        },
    },
}


# =============================================================================
# ACORD 125/140 Field Schema
# =============================================================================

BROKER_ACORD_FIELD_SCHEMA = {
    "name": "BrokerAcordFields",
    "description": "Extract ACORD 125 and ACORD 140 fields from commercial property submission documents (SOV, loss runs, prior policies)",
    "fields": {
        # ACORD 125 fields
        "ApplicantName": {
            "type": "string",
            "method": "extract",
            "description": "Full legal name of the applicant/insured",
        },
        "FEIN": {
            "type": "string",
            "method": "extract",
            "description": "Federal Employer Identification Number",
        },
        "BusinessPhone": {
            "type": "string",
            "method": "extract",
            "description": "Business phone number",
        },
        "MailingAddress": {
            "type": "string",
            "method": "extract",
            "description": "Full mailing address",
        },
        "BusinessType": {
            "type": "string",
            "method": "extract",
            "description": "Business entity type (LLC, Corporation, Partnership, etc.)",
        },
        "YearsInBusiness": {
            "type": "string",
            "method": "extract",
            "description": "Number of years in business",
        },
        "SICCode": {
            "type": "string",
            "method": "extract",
            "description": "Standard Industrial Classification code",
        },
        "NAICSCode": {
            "type": "string",
            "method": "extract",
            "description": "North American Industry Classification System code",
        },
        "AnnualGrossRevenue": {
            "type": "string",
            "method": "extract",
            "description": "Annual gross revenue",
        },
        "NumberOfEmployees": {
            "type": "string",
            "method": "extract",
            "description": "Total number of employees",
        },
        "PriorCarrier": {
            "type": "string",
            "method": "extract",
            "description": "Prior insurance carrier name",
        },
        "PriorPolicyNumber": {
            "type": "string",
            "method": "extract",
            "description": "Prior policy number",
        },
        "PriorPremium": {
            "type": "string",
            "method": "extract",
            "description": "Prior policy premium amount",
        },
        "PriorExpirationDate": {
            "type": "date",
            "method": "extract",
            "description": "Prior policy expiration date",
        },
        "EffectiveDateRequested": {
            "type": "date",
            "method": "extract",
            "description": "Requested effective date for new coverage",
        },
        "CurrentCoverageLimits": {
            "type": "string",
            "method": "extract",
            "description": "Current coverage limits",
        },
        "CurrentDeductibles": {
            "type": "string",
            "method": "extract",
            "description": "Current deductibles",
        },
        "RequestedCoverageLimits": {
            "type": "string",
            "method": "extract",
            "description": "Requested coverage limits for new policy",
        },
        "RequestedDeductibles": {
            "type": "string",
            "method": "extract",
            "description": "Requested deductibles for new policy",
        },
        "LinesOfBusinessRequested": {
            "type": "string",
            "method": "extract",
            "description": "Lines of business requested",
        },
        "CoverageModifications": {
            "type": "string",
            "method": "extract",
            "description": "Coverage modifications or changes requested (e.g. add equipment breakdown, increase BI limit)",
        },
        # ACORD 140 fields
        "PropertyLocations": {
            "type": "array",
            "method": "extract",
            "description": "List of property locations with details",
            "items": {
                "type": "object",
                "properties": {
                    "Address": {
                        "type": "string",
                        "description": "Full property address",
                    },
                    "BuildingValue": {
                        "type": "string",
                        "description": "Building replacement value",
                    },
                    "ContentsValue": {
                        "type": "string",
                        "description": "Contents/BPP value",
                    },
                    "ConstructionType": {
                        "type": "string",
                        "description": "Construction type/class",
                    },
                    "OccupancyType": {
                        "type": "string",
                        "description": "Occupancy type",
                    },
                    "YearBuilt": {
                        "type": "string",
                        "description": "Year built",
                    },
                    "SquareFootage": {
                        "type": "string",
                        "description": "Total square footage",
                    },
                    "SprinklerSystem": {
                        "type": "string",
                        "description": "Sprinkler type",
                    },
                    "RoofType": {
                        "type": "string",
                        "description": "Roof type and condition",
                    },
                    "FloodZone": {
                        "type": "string",
                        "description": "FEMA flood zone designation",
                    },
                    "ProtectionClass": {
                        "type": "string",
                        "description": "Fire protection class",
                    },
                },
            },
        },
        "LossHistory": {
            "type": "array",
            "method": "extract",
            "description": "Loss history entries from loss runs",
            "items": {
                "type": "object",
                "properties": {
                    "DateOfLoss": {
                        "type": "date",
                        "description": "Date the loss occurred",
                    },
                    "CauseOfLoss": {
                        "type": "string",
                        "description": "Cause or type of loss",
                    },
                    "Location": {
                        "type": "string",
                        "description": "Location where loss occurred",
                    },
                    "AmountPaid": {
                        "type": "string",
                        "description": "Amount paid on the claim",
                    },
                    "AmountReserved": {
                        "type": "string",
                        "description": "Amount reserved",
                    },
                    "TotalIncurred": {
                        "type": "string",
                        "description": "Total incurred (paid + reserved)",
                    },
                    "Status": {
                        "type": "string",
                        "description": "Claim status (Open/Closed)",
                    },
                    "Description": {
                        "type": "string",
                        "description": "Description of the loss event",
                    },
                },
            },
        },
        "TotalInsuredValue": {
            "type": "string",
            "method": "extract",
            "description": "Combined total insured value across all locations",
        },
        "MortgageeInfo": {
            "type": "string",
            "method": "extract",
            "description": "Mortgagee/lender information",
        },
        "SpecialConditions": {
            "type": "array",
            "method": "extract",
            "description": "Special conditions or hazards noted",
            "items": {"type": "string"},
        },
    },
}


# =============================================================================
# Research / AM Best Field Schema
# =============================================================================

BROKER_RESEARCH_FIELD_SCHEMA = {
    "name": "BrokerResearchFields",
    "description": "Extract carrier financial and rating data from AM Best credit reports and MD&A documents",
    "fields": {
        "CarrierName": {
            "type": "string",
            "method": "extract",
            "description": "Full legal name of the insurance carrier",
        },
        "AMBNumber": {
            "type": "string",
            "method": "extract",
            "description": "AM Best company number",
        },
        "NAICCode": {
            "type": "string",
            "method": "extract",
            "description": "NAIC company code",
        },
        "FinancialStrengthRating": {
            "type": "string",
            "method": "extract",
            "description": "AM Best Financial Strength Rating (e.g. A+, A, B++)",
        },
        "IssuerCreditRating": {
            "type": "string",
            "method": "extract",
            "description": "AM Best Issuer Credit Rating (e.g. aa, a+)",
        },
        "RatingOutlook": {
            "type": "string",
            "method": "extract",
            "description": "Rating outlook (Stable, Positive, Negative, Developing)",
        },
        "BalanceSheetStrength": {
            "type": "string",
            "method": "extract",
            "description": "Balance sheet strength assessment",
        },
        "OperatingPerformance": {
            "type": "string",
            "method": "extract",
            "description": "Operating performance assessment",
        },
        "BusinessProfile": {
            "type": "string",
            "method": "extract",
            "description": "Business profile assessment",
        },
        "ERMAssessment": {
            "type": "string",
            "method": "extract",
            "description": "Enterprise Risk Management assessment",
        },
        "NetPremiumsWritten": {
            "type": "string",
            "method": "extract",
            "description": "Net premiums written (latest year)",
        },
        "PolicyholdersSurplus": {
            "type": "string",
            "method": "extract",
            "description": "Policyholders surplus",
        },
        "CombinedRatio": {
            "type": "string",
            "method": "extract",
            "description": "Combined ratio (latest year)",
        },
        "FiveYearAvgCombinedRatio": {
            "type": "string",
            "method": "extract",
            "description": "Five-year average combined ratio",
        },
        "DirectWrittenPremium": {
            "type": "string",
            "method": "extract",
            "description": "Direct written premium",
        },
        "NWPToSurplusRatio": {
            "type": "string",
            "method": "extract",
            "description": "Net written premium to surplus ratio",
        },
        "LinesOfBusinessWritten": {
            "type": "array",
            "method": "extract",
            "description": "Lines of business written",
            "items": {"type": "string"},
        },
        "GeographicConcentration": {
            "type": "string",
            "method": "extract",
            "description": "Geographic concentration or operating territory",
        },
        "ReportDate": {
            "type": "date",
            "method": "extract",
            "description": "Date of the report",
        },
        "KeyFinancialHighlights": {
            "type": "array",
            "method": "extract",
            "description": "Key financial highlights or summary points",
            "items": {"type": "string"},
        },
    },
}
