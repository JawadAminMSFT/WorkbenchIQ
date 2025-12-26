"""
Category Inference - Infer policy categories from natural language queries.

Provides keyword-based and optional LLM-based category inference for search filtering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.utils import setup_logging

if TYPE_CHECKING:
    from app.config import OpenAISettings

logger = setup_logging()


# Keyword mappings for category inference
# Keys are categories, values are lists of keywords/patterns
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cardiovascular": [
        # Blood pressure
        r"\bblood\s*pressure\b",
        r"\bbp\b",
        r"\bhypertension\b",
        r"\bhypotension\b",
        r"\bsystolic\b",
        r"\bdiastolic\b",
        r"\bmmhg\b",
        r"\b\d{2,3}\s*/\s*\d{2,3}\b",  # e.g., 140/90
        # Heart conditions
        r"\bheart\b",
        r"\bcardiac\b",
        r"\bcardio\b",
        r"\barrhythmia\b",
        r"\batrial\s*fib",
        r"\bafib\b",
        r"\bchf\b",
        r"\bheart\s*failure\b",
        r"\bcad\b",
        r"\bcoronary\b",
        r"\bangina\b",
        r"\bmyocardial\b",
        r"\bmi\b",
        r"\bheart\s*attack\b",
        r"\bstroke\b",
        r"\bcvd\b",
        r"\bpalpitation\b",
        r"\bmurmur\b",
        r"\bvalve\b",
    ],
    "metabolic": [
        # Cholesterol
        r"\bcholesterol\b",
        r"\bldl\b",
        r"\bhdl\b",
        r"\btriglyceride\b",
        r"\blipid\b",
        r"\bstatin\b",
        r"\bhyperlipidemia\b",
        r"\bdyslipidemia\b",
        # Weight/BMI
        r"\bbmi\b",
        r"\bbody\s*mass\b",
        r"\bobes",  # obesity, obese
        r"\boverweight\b",
        r"\bunderweight\b",
        r"\bweight\b",
        r"\bheight\b",
        r"\bkg\b",
        r"\blbs?\b",
        r"\bpounds?\b",
        # Liver
        r"\bast\b",
        r"\balt\b",
        r"\bliver\s*function\b",
        r"\blft\b",
        r"\bhepatic\b",
        r"\bfatty\s*liver\b",
        r"\bcirrhosis\b",
        r"\bhepatitis\b",
        # Diabetes (also metabolic - blood sugar regulation)
        r"\bdiabetes\b",
        r"\bdiabetic\b",
        r"\bglucose\b",
        r"\bblood\s*sugar\b",
        r"\bhba1c\b",
        r"\ba1c\b",
    ],
    "endocrine": [
        # Diabetes
        r"\bdiabetes\b",
        r"\bdiabetic\b",
        r"\bglucose\b",
        r"\bblood\s*sugar\b",
        r"\binsulin\b",
        r"\bhba1c\b",
        r"\ba1c\b",
        r"\bfasting\s*(blood\s*)?sugar\b",
        r"\bfbs\b",
        r"\btype\s*[12]\b",
        r"\bt[12]dm\b",
        r"\bhyperglycemia\b",
        r"\bhypoglycemia\b",
        r"\bmetformin\b",
        # Thyroid
        r"\bthyroid\b",
        r"\btsh\b",
        r"\bhypothyroid",
        r"\bhyperthyroid",
        r"\blevothyroxine\b",
        r"\bsynthroid\b",
    ],
    "family_history": [
        r"\bfamily\s*history\b",
        r"\bfamilial\b",
        r"\bhereditary\b",
        r"\bgenetic\b",
        r"\binherited\b",
        r"\bparent\b",
        r"\bmother\b",
        r"\bfather\b",
        r"\bsibling\b",
        r"\bbrother\b",
        r"\bsister\b",
        r"\bgrandparent\b",
        r"\brelative\b",
        r"\bpremature\s*death\b",
        r"\bcancer\s*(history|risk)\b",
        r"\bheart\s*disease\s*(family|history)\b",
    ],
    "lifestyle": [
        # Smoking
        r"\bsmok",  # smoke, smoking, smoker
        r"\btobacco\b",
        r"\bcigarette\b",
        r"\bnicotine\b",
        r"\bvap(e|ing)\b",
        r"\bpack\s*year\b",
        r"\bnon-?smoker\b",
        r"\bex-?smoker\b",
        # Alcohol
        r"\balcohol\b",
        r"\bdrink",  # drink, drinking
        r"\bbeer\b",
        r"\bwine\b",
        r"\bspirits\b",
        r"\bunits?\s*(per|/)\s*(week|day)\b",
        r"\bsober\b",
        r"\babstinent\b",
        # Drugs
        r"\bdrug\s*use\b",
        r"\bsubstance\b",
        r"\bmarijuana\b",
        r"\bcannabis\b",
        r"\bcocaine\b",
        r"\bheroin\b",
        r"\bopioid\b",
        r"\brecreational\b",
    ],
}

# Subcategory keywords for more specific inference
SUBCATEGORY_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "cardiovascular": {
        "hypertension": [
            r"\bblood\s*pressure\b",
            r"\bhypertension\b",
            r"\bsystolic\b",
            r"\bdiastolic\b",
            r"\b\d{2,3}\s*/\s*\d{2,3}\b",
        ],
        "arrhythmia": [
            r"\barrhythmia\b",
            r"\batrial\s*fib",
            r"\bafib\b",
            r"\bpalpitation\b",
        ],
        "coronary_artery_disease": [
            r"\bcad\b",
            r"\bcoronary\b",
            r"\bangina\b",
            r"\bheart\s*attack\b",
        ],
    },
    "metabolic": {
        "cholesterol": [
            r"\bcholesterol\b",
            r"\bldl\b",
            r"\bhdl\b",
            r"\btriglyceride\b",
            r"\blipid\b",
        ],
        "bmi": [
            r"\bbmi\b",
            r"\bbody\s*mass\b",
            r"\bobes",
            r"\boverweight\b",
            r"\bweight\b",
        ],
        "liver_function": [
            r"\bast\b",
            r"\balt\b",
            r"\bliver\b",
            r"\blft\b",
        ],
    },
    "endocrine": {
        "diabetes": [
            r"\bdiabetes\b",
            r"\bdiabetic\b",
            r"\bglucose\b",
            r"\bhba1c\b",
            r"\binsulin\b",
        ],
        "thyroid": [
            r"\bthyroid\b",
            r"\btsh\b",
        ],
    },
    "lifestyle": {
        "smoking": [
            r"\bsmok",
            r"\btobacco\b",
            r"\bcigarette\b",
            r"\bnicotine\b",
        ],
        "alcohol": [
            r"\balcohol\b",
            r"\bdrink",
            r"\bbeer\b",
            r"\bwine\b",
        ],
        "substance_use": [
            r"\bdrug\s*use\b",
            r"\bsubstance\b",
            r"\bmarijuana\b",
        ],
    },
}

# Risk level keywords
RISK_LEVEL_KEYWORDS: dict[str, list[str]] = {
    "High": [
        r"\bsevere\b",
        r"\bcritical\b",
        r"\bdangerous\b",
        r"\bextreme\b",
        r"\buncontrolled\b",
        r"\bpoor\s*control\b",
        r"\bcomplications\b",
        r"\bhospitalized?\b",
    ],
    "Moderate": [
        r"\bmoderate\b",
        r"\belevated\b",
        r"\bborderline\b",
        r"\bcontrolled\b",
        r"\bmedication\b",
        r"\btreatment\b",
    ],
    "Low": [
        r"\bnormal\b",
        r"\bhealthy\b",
        r"\boptimal\b",
        r"\bwell\s*controlled\b",
        r"\bno\s*(issues?|problems?|concerns?)\b",
    ],
}


@dataclass
class InferredContext:
    """Result of category/context inference from a query."""
    
    categories: list[str]
    subcategories: list[str]
    risk_levels: list[str]
    confidence: float
    method: str  # "keyword" or "llm"
    
    def has_filters(self) -> bool:
        """Check if any filters were inferred."""
        return bool(self.categories or self.subcategories or self.risk_levels)


class CategoryInference:
    """
    Infers policy categories and context from natural language queries.
    
    Supports:
    - Keyword-based inference (fast, rule-based)
    - Optional LLM-based inference (more accurate, slower)
    """
    
    def __init__(self, openai_settings: "OpenAISettings | None" = None):
        """
        Initialize inference service.
        
        Args:
            openai_settings: Optional OpenAI settings for LLM-based inference
        """
        self.openai_settings = openai_settings
        
        # Compile regex patterns for performance
        self._category_patterns = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in CATEGORY_KEYWORDS.items()
        }
        self._subcategory_patterns = {
            cat: {
                subcat: [re.compile(p, re.IGNORECASE) for p in patterns]
                for subcat, patterns in subcats.items()
            }
            for cat, subcats in SUBCATEGORY_KEYWORDS.items()
        }
        self._risk_patterns = {
            level: [re.compile(p, re.IGNORECASE) for p in patterns]
            for level, patterns in RISK_LEVEL_KEYWORDS.items()
        }
    
    def infer_from_keywords(self, query: str) -> InferredContext:
        """
        Infer categories using keyword matching.
        
        Args:
            query: Natural language query
            
        Returns:
            InferredContext with matched categories
        """
        categories = []
        subcategories = []
        risk_levels = []
        match_scores: dict[str, int] = {}
        
        # Match categories
        for category, patterns in self._category_patterns.items():
            matches = sum(1 for p in patterns if p.search(query))
            if matches > 0:
                categories.append(category)
                match_scores[category] = matches
        
        # Match subcategories for matched categories
        for category in categories:
            if category in self._subcategory_patterns:
                for subcat, patterns in self._subcategory_patterns[category].items():
                    if any(p.search(query) for p in patterns):
                        subcategories.append(subcat)
        
        # Match risk levels
        for level, patterns in self._risk_patterns.items():
            if any(p.search(query) for p in patterns):
                risk_levels.append(level)
        
        # Calculate confidence based on number of matches
        total_matches = sum(match_scores.values())
        confidence = min(1.0, total_matches * 0.2) if total_matches > 0 else 0.0
        
        result = InferredContext(
            categories=categories,
            subcategories=subcategories,
            risk_levels=risk_levels,
            confidence=confidence,
            method="keyword",
        )
        
        logger.debug(
            f"Keyword inference: query='{query[:50]}...' "
            f"categories={categories} subcategories={subcategories}"
        )
        
        return result
    
    async def infer_with_llm(self, query: str) -> InferredContext:
        """
        Infer categories using LLM for better understanding.
        
        Requires OpenAI settings to be configured.
        
        Args:
            query: Natural language query
            
        Returns:
            InferredContext with LLM-inferred categories
        """
        if not self.openai_settings:
            logger.warning("LLM inference requested but OpenAI not configured")
            return self.infer_from_keywords(query)
        
        try:
            from openai import AzureOpenAI
            
            client = AzureOpenAI(
                api_key=self.openai_settings.api_key,
                api_version=self.openai_settings.api_version,
                azure_endpoint=self.openai_settings.endpoint,
            )
            
            # Available categories from our policies
            available_categories = list(CATEGORY_KEYWORDS.keys())
            
            prompt = f"""Analyze this underwriting query and identify relevant categories.

Query: "{query}"

Available categories: {', '.join(available_categories)}

Respond with a JSON object:
{{
    "categories": ["list of matching categories from available options"],
    "risk_level_hint": "Low/Moderate/High or null if unclear",
    "confidence": 0.0-1.0
}}

Only include categories that are clearly relevant. Respond with valid JSON only."""

            response = client.chat.completions.create(
                model=self.openai_settings.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an insurance underwriting assistant. Analyze queries to identify relevant policy categories."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )
            
            import json
            result_text = response.choices[0].message.content or "{}"
            
            # Clean up response - remove markdown code blocks if present
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text.rsplit("```", 1)[0]
            result_text = result_text.strip()
            
            parsed = json.loads(result_text)
            
            categories = [c for c in parsed.get("categories", []) if c in available_categories]
            risk_hint = parsed.get("risk_level_hint")
            risk_levels = [risk_hint] if risk_hint in ["Low", "Moderate", "High"] else []
            
            return InferredContext(
                categories=categories,
                subcategories=[],  # LLM doesn't infer subcategories currently
                risk_levels=risk_levels,
                confidence=parsed.get("confidence", 0.7),
                method="llm",
            )
            
        except Exception as e:
            logger.warning(f"LLM inference failed, falling back to keywords: {e}")
            return self.infer_from_keywords(query)
    
    def infer(self, query: str, use_llm: bool = False) -> InferredContext:
        """
        Synchronous inference (keyword-based only).
        
        Args:
            query: Natural language query
            use_llm: Ignored in sync mode (use infer_with_llm for async)
            
        Returns:
            InferredContext
        """
        return self.infer_from_keywords(query)
    
    async def infer_async(
        self,
        query: str,
        use_llm: bool = False,
        llm_threshold: float = 0.3,
    ) -> InferredContext:
        """
        Async inference with optional LLM fallback.
        
        Uses keyword inference first. If confidence is below threshold
        and use_llm is True, falls back to LLM inference.
        
        Args:
            query: Natural language query
            use_llm: Whether to use LLM if keyword confidence is low
            llm_threshold: Confidence threshold below which to use LLM
            
        Returns:
            InferredContext
        """
        # Always try keywords first (fast)
        keyword_result = self.infer_from_keywords(query)
        
        # If high confidence or LLM disabled, return keyword result
        if not use_llm or keyword_result.confidence >= llm_threshold:
            return keyword_result
        
        # Try LLM for better inference
        return await self.infer_with_llm(query)
