"""
Document type classifier for Canadian mortgage underwriting documents.

Classifies documents by filename patterns with content-based fallback.
"""

import re
from typing import Optional


class MortgageDocClassifier:
    """
    Classifies mortgage documents based on filename patterns.
    
    Supports Canadian mortgage document types:
    - Income: T4, pay stubs, employment letters, NOA
    - Property: Appraisals, purchase agreements
    - Financial: Bank statements, gift letters, credit reports
    - Application: Mortgage application summaries
    """
    
    # Filename patterns for document classification
    # Order matters - more specific patterns first
    FILENAME_PATTERNS = [
        # Income documents
        (r'\bt4[_\s-]?\d*\.', 't4'),
        (r't4[_\s]?(statement|slip|form)', 't4'),
        (r'(pay[_\s]?stub|paystub)', 'pay_stub'),
        (r'pay[_\s]?(slip|cheque|check)', 'pay_stub'),
        (r'(employment[_\s]?letter|letter[_\s]?of[_\s]?employment)', 'employment_letter'),
        (r'(confirmation[_\s]?(of[_\s]?)?employment)', 'employment_letter'),
        (r'(job[_\s]?letter)', 'employment_letter'),
        (r'(noa|notice[_\s]?(of[_\s]?)?assessment)', 'notice_of_assessment'),
        (r't1[_\s]?(general)?', 't1_general'),
        
        # Property documents
        (r'(appraisal|property[_\s]?appraisal|appraisal[_\s]?report)', 'appraisal_report'),
        (r'(purchase[_\s]?(sale[_\s]?)?agreement|agreement[_\s]?(of[_\s]?)?purchase)', 'purchase_sale_agreement'),
        (r'(sale[_\s]?agreement|aps)', 'purchase_sale_agreement'),
        (r'(property[_\s]?tax|tax[_\s]?bill)', 'property_tax_bill'),
        (r'(title[_\s]?search|title[_\s]?report)', 'title_search'),
        (r'(condo[_\s]?(doc|status|cert))', 'condo_documents'),
        
        # Financial documents
        (r'(bank[_\s]?statement|statement)', 'bank_statement'),
        (r'(chequing|checking|savings)[_\s]?statement', 'bank_statement'),
        (r'(gift[_\s]?letter)', 'gift_letter'),
        (r'(credit[_\s]?report|equifax|transunion)', 'credit_report'),
        (r'(rrsp|tfsa)[_\s]?(statement)?', 'rrsp_statement'),
        (r'(down[_\s]?payment|dp[_\s]?verification)', 'down_payment_verification'),
        
        # Application documents
        (r'(mortgage[_\s]?application|application[_\s]?(form|summary)?)', 'application_summary'),
        (r'(loan[_\s]?application)', 'application_summary'),
        
        # Insurance
        (r'(home[_\s]?(owners?)?[_\s]?insurance|insurance[_\s]?policy)', 'homeowners_insurance'),
        (r'(cmhc|mortgage[_\s]?insurance)', 'mortgage_insurance'),
        
        # ID verification
        (r'(id[_\s]?(verification|document)|drivers?[_\s]?licen[cs]e|passport)', 'id_verification'),
    ]
    
    def __init__(self):
        """Initialize classifier with compiled regex patterns."""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), doc_type)
            for pattern, doc_type in self.FILENAME_PATTERNS
        ]
    
    def classify_document(
        self,
        content: bytes,
        filename: str,
        content_hint: Optional[str] = None
    ) -> str:
        """
        Classify a mortgage document based on filename and optionally content.
        
        Args:
            content: Raw document bytes (for future content-based classification)
            filename: Original filename of the document
            content_hint: Optional hint from OCR or metadata
            
        Returns:
            Document type string (e.g., 't4', 'pay_stub', 'appraisal_report')
        """
        # Try filename-based classification first
        doc_type = self._classify_by_filename(filename)
        if doc_type:
            return doc_type
        
        # Try content hint if provided
        if content_hint:
            doc_type = self._classify_by_content_hint(content_hint)
            if doc_type:
                return doc_type
        
        # Default to 'other' for unknown documents
        return "other"
    
    def _classify_by_filename(self, filename: str) -> Optional[str]:
        """
        Classify document by filename pattern matching.
        
        Args:
            filename: Original filename
            
        Returns:
            Document type or None if no match
        """
        filename_lower = filename.lower()
        
        for pattern, doc_type in self._compiled_patterns:
            if pattern.search(filename_lower):
                return doc_type
        
        return None
    
    def _classify_by_content_hint(self, content_hint: str) -> Optional[str]:
        """
        Classify document by content hint (OCR text or metadata).
        
        Args:
            content_hint: Text extracted from document
            
        Returns:
            Document type or None if no match
        """
        hint_lower = content_hint.lower()
        
        # Look for key phrases in content
        content_patterns = [
            (r'statement of remuneration paid', 't4'),
            (r't4 summary', 't4'),
            (r'notice of assessment', 'notice_of_assessment'),
            (r'employment income', 'pay_stub'),
            (r'net pay|gross pay|ytd earnings', 'pay_stub'),
            (r'this is to confirm.*employ', 'employment_letter'),
            (r'appraisal report|market value estimate', 'appraisal_report'),
            (r'agreement of purchase and sale', 'purchase_sale_agreement'),
            (r'credit score|credit bureau', 'credit_report'),
            (r'gift.*amount.*funds', 'gift_letter'),
        ]
        
        for pattern, doc_type in content_patterns:
            if re.search(pattern, hint_lower):
                return doc_type
        
        return None
    
    def get_supported_types(self) -> list[str]:
        """Return list of all supported document types."""
        return list(set(doc_type for _, doc_type in self.FILENAME_PATTERNS))
