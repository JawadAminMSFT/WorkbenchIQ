"""
Document router for Canadian mortgage underwriting.

Routes classified documents to the appropriate Azure Content Understanding analyzer.
"""

from typing import Tuple

from app.config import MortgageUnderwritingSettings
from app.mortgage.doc_classifier import MortgageDocClassifier


class MortgageDocRouter:
    """
    Routes mortgage documents to the appropriate analyzer based on document type.
    
    Currently all mortgage documents use a single mortgageDocAnalyzer,
    but this architecture supports future expansion to specialized analyzers
    (e.g., separate income vs property analyzers).
    """
    
    # Document types that have specialized field extraction
    INCOME_DOCS = {'t4', 'pay_stub', 'employment_letter', 'notice_of_assessment', 't1_general'}
    PROPERTY_DOCS = {'appraisal_report', 'purchase_sale_agreement', 'property_tax_bill', 'title_search'}
    FINANCIAL_DOCS = {'bank_statement', 'credit_report', 'rrsp_statement', 'gift_letter'}
    APPLICATION_DOCS = {'application_summary'}
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    
    def __init__(self):
        """Initialize router with document classifier."""
        self._classifier = MortgageDocClassifier()
    
    def route_document(
        self,
        content: bytes,
        filename: str,
        settings: MortgageUnderwritingSettings
    ) -> Tuple[str, str]:
        """
        Route a document to the appropriate analyzer.
        
        Args:
            content: Raw document bytes
            filename: Original filename
            settings: Mortgage underwriting settings
            
        Returns:
            Tuple of (doc_type, analyzer_id)
        """
        # Classify the document
        doc_type = self._classifier.classify_document(content, filename)
        
        # Get the appropriate analyzer
        analyzer_id = self.get_analyzer_id(doc_type, settings)
        
        return (doc_type, analyzer_id)
    
    def get_analyzer_id(
        self,
        doc_type: str,
        settings: MortgageUnderwritingSettings
    ) -> str:
        """
        Get the analyzer ID for a given document type.
        
        Currently returns the single mortgageDocAnalyzer for all types.
        Future versions may route to specialized analyzers.
        
        Args:
            doc_type: Document type from classifier
            settings: Mortgage underwriting settings
            
        Returns:
            Azure Content Understanding analyzer ID
        """
        # For now, all mortgage documents use the same analyzer
        # Future: Could route income docs to incomeAnalyzer, etc.
        return settings.doc_analyzer
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Validate that the file type is supported.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if file type is supported
        """
        import os
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_document_category(self, doc_type: str) -> str:
        """
        Get the category for a document type.
        
        Args:
            doc_type: Document type
            
        Returns:
            Category string: 'income', 'property', 'financial', 'application', 'other'
        """
        if doc_type in self.INCOME_DOCS:
            return 'income'
        elif doc_type in self.PROPERTY_DOCS:
            return 'property'
        elif doc_type in self.FINANCIAL_DOCS:
            return 'financial'
        elif doc_type in self.APPLICATION_DOCS:
            return 'application'
        else:
            return 'other'
