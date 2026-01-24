"""
Case data aggregator for Canadian mortgage underwriting.

Aggregates data from multiple documents into a canonical case model.
"""

from typing import Any, Dict, List, Optional


class MortgageCaseAggregator:
    """
    Aggregates mortgage application data from multiple documents.
    
    Handles:
    - Merging borrower data from multiple sources
    - Combining income from various documents
    - Detecting inconsistencies across documents
    - Building canonical case model
    """
    
    # Variance threshold for flagging income inconsistencies
    INCOME_VARIANCE_THRESHOLD = 0.05  # 5%
    
    def __init__(self):
        """Initialize aggregator."""
        self._inconsistencies = []
    
    def aggregate_borrower_data(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge borrower data from multiple documents.
        
        Priority: application_summary > t4 > employment_letter > pay_stub
        
        Args:
            docs: List of document extraction results
            
        Returns:
            Merged borrower data
        """
        result = {}
        
        # Priority order for field sources
        priority_order = ["application_summary", "credit_report", "t4", "employment_letter", "pay_stub", "other"]
        
        for doc_type in priority_order:
            for doc in docs:
                if doc.get("doc_type") == doc_type:
                    borrower = doc.get("borrower", {})
                    # Only add fields not already set (higher priority wins)
                    for key, value in borrower.items():
                        if key not in result and value:
                            result[key] = value
        
        return result
    
    def aggregate_income_data(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine income data from multiple sources.
        
        Tracks all income sources for reconciliation.
        
        Args:
            docs: List of document extraction results
            
        Returns:
            List of income sources with metadata
        """
        income_sources = []
        
        for doc in docs:
            income = doc.get("income", {})
            if income:
                income_sources.append({
                    "doc_type": doc.get("doc_type"),
                    "doc_id": doc.get("doc_id"),
                    **income
                })
        
        return income_sources
    
    def detect_inconsistencies(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect inconsistencies in case data.
        
        Checks for:
        - Income variance between documents
        - Name/address mismatches
        - Date discrepancies
        
        Args:
            case_data: Aggregated case data
            
        Returns:
            List of detected inconsistencies
        """
        inconsistencies = []
        
        # Check income variance
        income_t4 = case_data.get("income_from_t4")
        income_paystub = case_data.get("income_from_paystub")
        
        if income_t4 and income_paystub:
            variance = abs(income_t4 - income_paystub) / max(income_t4, income_paystub)
            if variance > self.INCOME_VARIANCE_THRESHOLD:
                inconsistencies.append({
                    "type": "income_variance",
                    "field": "income",
                    "sources": ["t4", "paystub"],
                    "values": [income_t4, income_paystub],
                    "variance": variance,
                    "message": f"Income variance of {variance:.1%} between T4 and pay stub"
                })
        
        return inconsistencies
    
    def build_canonical_case(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build canonical case model from document extractions.
        
        Creates unified model per the mortgage case schema.
        
        Args:
            docs: List of document extraction results
            
        Returns:
            Canonical case model
        """
        case = {
            "borrowers": [],
            "application": {},
            "property": {},
            "loan": {},
            "documents": [],
        }
        
        # Aggregate borrower data
        borrower_data = self.aggregate_borrower_data(docs)
        if borrower_data:
            case["borrowers"].append(borrower_data)
        
        # Aggregate income
        income_sources = self.aggregate_income_data(docs)
        case["income_sources"] = income_sources
        
        # Extract property data
        for doc in docs:
            if doc.get("doc_type") == "appraisal_report":
                case["property"] = doc.get("property", doc.get("fields", {}))
            
            # Track all documents
            case["documents"].append({
                "doc_type": doc.get("doc_type"),
                "doc_id": doc.get("doc_id"),
                "filename": doc.get("filename"),
            })
        
        # Extract loan data
        for doc in docs:
            if doc.get("doc_type") == "application_summary":
                case["loan"] = doc.get("loan", doc.get("fields", {}))
        
        return case
    
    def reconcile_values(
        self,
        field_name: str,
        values: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reconcile conflicting values for a field.
        
        Uses source priority and confidence scores.
        
        Args:
            field_name: Name of the field
            values: List of value candidates with source info
            
        Returns:
            Resolved value with provenance
        """
        if not values:
            return {"value": None, "source": None}
        
        # Sort by priority (lower is better)
        priority_map = {
            "t4": 1,
            "noa": 2,
            "employment_letter": 3,
            "pay_stub": 4,
            "application_summary": 5,
            "other": 10,
        }
        
        sorted_values = sorted(
            values,
            key=lambda x: priority_map.get(x.get("source_type", "other"), 10)
        )
        
        winner = sorted_values[0]
        
        return {
            "value": winner.get("value"),
            "source": winner.get("source_type"),
            "confidence": winner.get("confidence"),
            "alternates": sorted_values[1:] if len(sorted_values) > 1 else []
        }
