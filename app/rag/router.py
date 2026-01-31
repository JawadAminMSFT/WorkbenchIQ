"""
RAG Query Router - Routes queries to appropriate persona/policy index.

Provides intelligent routing of user queries to the correct policy index
based on query content and explicit persona parameters.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RouteResult:
    """Result of query routing."""
    
    persona: str
    confidence: float
    matched_keywords: List[str]
    
    def __str__(self) -> str:
        return self.persona


# Keyword patterns for persona detection
PERSONA_KEYWORDS = {
    "mortgage_underwriting": [
        # OSFI B-20 terms
        r"\bgds\b", r"\btds\b", r"\bltv\b", r"\bmqr\b",
        r"\bdown\s*payment\b", r"\bqualifying\s*rate\b",
        r"\bstress\s*test\b", r"\bamortization\b",
        # Canadian mortgage terms
        r"\bmortgage\b", r"\bcmhc\b", r"\bgenworth\b",
        r"\binsured\s*mortgage\b", r"\buninsured\s*mortgage\b",
        r"\bconventional\s*mortgage\b",
        # OSFI references
        r"\bosfi\b", r"\bb-20\b", r"\bguideline\b",
        # Income/debt terms
        r"\bdebt\s*service\b", r"\bgross\s*debt\b", r"\btotal\s*debt\b",
        r"\bpiti\b", r"\bhousing\s*costs?\b",
    ],
    "underwriting": [
        r"\bunderwriting\b", r"\blife\s*insurance\b",
        r"\bhealth\s*insurance\b", r"\brisk\s*assessment\b",
        r"\bpolicy\s*limits?\b", r"\bmedical\s*history\b",
        r"\bpremium\b", r"\bcoverage\b",
    ],
    "life_health_claims": [
        r"\blife\s*claim\b", r"\bhealth\s*claim\b",
        r"\bdeath\s*benefit\b", r"\bdisability\b",
        r"\bhospital\b", r"\bmedical\s*claim\b",
    ],
    "automotive_claims": [
        r"\bauto\s*claim\b", r"\bcar\s*accident\b",
        r"\bvehicle\s*damage\b", r"\bcollision\b",
        r"\bliability\b", r"\bcomprehensive\b",
        r"\bautomotive\b", r"\bmotor\s*vehicle\b",
    ],
    "property_casualty_claims": [
        r"\bproperty\s*claim\b", r"\bproperty\s*damage\b",
        r"\bhomeowner\b", r"\bflood\b", r"\bfire\b",
        r"\btheft\b", r"\bcasualty\b", r"\bliability\s*claim\b",
    ],
}


class QueryRouter:
    """
    Routes queries to the appropriate persona/policy index.
    
    Routing strategies:
    1. Explicit persona: If persona is provided, use it
    2. Keyword matching: Match query keywords to persona patterns
    3. Default fallback: Use default persona if no match
    """
    
    def __init__(
        self,
        default_persona: str = "underwriting",
        min_confidence: float = 0.3,
    ):
        """
        Initialize router.
        
        Args:
            default_persona: Default persona when no match found
            min_confidence: Minimum confidence to route to detected persona
        """
        self.default_persona = default_persona
        self.min_confidence = min_confidence
        
        # Compile regex patterns
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for persona, patterns in PERSONA_KEYWORDS.items():
            self._compiled_patterns[persona] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def route(
        self,
        query: str,
        persona: Optional[str] = None,
    ) -> str:
        """
        Route a query to the appropriate persona.
        
        Args:
            query: User query text
            persona: Explicit persona override
            
        Returns:
            Persona name string
        """
        # Explicit persona takes precedence
        if persona:
            return persona
        
        # Detect persona from query
        result = self.detect_persona(query)
        
        if result.confidence >= self.min_confidence:
            return result.persona
        
        return self.default_persona
    
    def detect_persona(self, query: str) -> RouteResult:
        """
        Detect the most likely persona from query content.
        
        Args:
            query: User query text
            
        Returns:
            RouteResult with persona, confidence, and matched keywords
        """
        scores: Dict[str, float] = {}
        matches: Dict[str, List[str]] = {}
        
        query_lower = query.lower()
        
        for persona, patterns in self._compiled_patterns.items():
            persona_matches = []
            
            for pattern in patterns:
                if pattern.search(query_lower):
                    persona_matches.append(pattern.pattern)
            
            if persona_matches:
                # Score based on number and quality of matches
                score = len(persona_matches) / len(patterns)
                scores[persona] = min(score * 2, 1.0)  # Scale up but cap at 1.0
                matches[persona] = persona_matches
        
        if not scores:
            return RouteResult(
                persona=self.default_persona,
                confidence=0.0,
                matched_keywords=[],
            )
        
        # Return highest scoring persona
        best_persona = max(scores, key=scores.get)
        return RouteResult(
            persona=best_persona,
            confidence=scores[best_persona],
            matched_keywords=matches.get(best_persona, []),
        )
    
    def get_supported_personas(self) -> List[str]:
        """Return list of supported personas."""
        return list(PERSONA_KEYWORDS.keys())
    
    def add_persona_keywords(
        self,
        persona: str,
        keywords: List[str],
    ) -> None:
        """
        Add keywords for a persona.
        
        Args:
            persona: Persona name
            keywords: List of regex patterns to match
        """
        if persona not in PERSONA_KEYWORDS:
            PERSONA_KEYWORDS[persona] = []
        
        PERSONA_KEYWORDS[persona].extend(keywords)
        
        # Recompile patterns
        self._compiled_patterns[persona] = [
            re.compile(p, re.IGNORECASE) for p in PERSONA_KEYWORDS[persona]
        ]
