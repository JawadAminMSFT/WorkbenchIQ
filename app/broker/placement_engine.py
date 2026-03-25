"""
Placement Engine Module

Scores and ranks carrier quotes using composite scoring methodology.
"""

from __future__ import annotations

import re
from typing import Dict, List

from app.broker.constants import CoverageAdequacy, PremiumBenchmark
from app.broker.models import CarrierProfile, PlacementScoring, Quote, Submission
from app.utils import setup_logging

logger = setup_logging()


class PlacementEngine:
    """Scores and ranks carrier quotes for optimal placement."""

    # Financial strength rating scoring
    FSR_SCORES = {
        "A++": 100,
        "A+": 100,
        "A": 85,
        "A-": 70,
        "B++": 50,
        "B+": 25,
    }
    UNRATED_SCORE = 10

    def score_quotes(
        self,
        quotes: List[Quote],
        submission: Submission,
        carrier_profiles: Dict[str, CarrierProfile],
    ) -> List[Quote]:
        """Score and rank quotes using composite scoring methodology.

        Scoring factors:
        - Premium competitiveness (35%)
        - Coverage completeness (30%)
        - Carrier financial strength (20%)
        - Quote completeness (15%)

        Args:
            quotes: List of Quote objects to score
            submission: Parent submission for context
            carrier_profiles: Dict mapping carrier names to CarrierProfile objects

        Returns:
            List of scored and ranked quotes (sorted by placement_score descending)
        """
        if not quotes:
            return []

        # Parse premium values for all quotes
        premium_data = []
        for quote in quotes:
            premium_value = self._parse_currency(quote.fields.annual_premium)
            coverage_breadth = self._calculate_coverage_breadth(quote)
            premium_data.append(
                {
                    "quote": quote,
                    "premium": premium_value,
                    "coverage_breadth": coverage_breadth,
                }
            )

        # Filter quotes with valid premiums
        valid_quotes = [pd for pd in premium_data if pd["premium"] > 0]
        if not valid_quotes:
            logger.warning("No quotes with valid premium values found")
            return quotes

        # Calculate premium range for normalization
        premiums = [pd["premium"] for pd in valid_quotes]
        min_premium = min(premiums)
        max_premium = max(premiums)
        premium_range = max_premium - min_premium if max_premium > min_premium else 1.0

        # Score each quote
        for pd in valid_quotes:
            quote = pd["quote"]
            premium = pd["premium"]
            coverage_breadth = pd["coverage_breadth"]

            # 1. Premium competitiveness (35%)
            # Lower premium = higher score, adjusted for coverage breadth
            if premium_range > 0:
                normalized_premium = (max_premium - premium) / premium_range
            else:
                normalized_premium = 0.5
            # Adjust for coverage differences (fewer exclusions = bonus)
            premium_adjustment = coverage_breadth * 0.1
            premium_score = (normalized_premium + premium_adjustment) * 35

            # 2. Coverage completeness (30%)
            coverage_score = self._calculate_coverage_score(quote) * 30

            # 3. Carrier financial strength (20%)
            carrier_profile = carrier_profiles.get(quote.carrier_name)
            financial_score = self._calculate_financial_score(
                quote, carrier_profile
            ) * 20

            # 4. Quote completeness (15%)
            completeness_score = self._calculate_completeness_score(quote) * 15

            # Composite score
            composite_score = (
                premium_score + coverage_score + financial_score + completeness_score
            )

            # Update quote scoring
            quote.scoring.placement_score = round(composite_score, 2)
            
            # Determine coverage adequacy
            quote.scoring.coverage_adequacy = self._determine_coverage_adequacy(quote)
            
            # Identify coverage gaps
            quote.scoring.coverage_gaps = self._identify_coverage_gaps(quote)
            
            # Determine premium benchmark
            quote.scoring.premium_percentile = self._determine_premium_percentile(
                premium, premiums
            )

        # Rank quotes by score
        valid_quote_objs = [pd["quote"] for pd in valid_quotes]
        valid_quote_objs.sort(key=lambda q: q.scoring.placement_score, reverse=True)
        
        for rank, quote in enumerate(valid_quote_objs, start=1):
            quote.scoring.placement_rank = rank
            
        # Generate recommendation for top quote
        if valid_quote_objs:
            top_quote = valid_quote_objs[0]
            top_quote.scoring.recommendation_rationale = self._build_rationale(
                top_quote, valid_quote_objs, carrier_profiles
            )

        return valid_quote_objs

    def generate_recommendation(self, quotes: List[Quote]) -> str:
        """Generate a plain-language recommendation for the best placement.

        Args:
            quotes: List of scored quotes (must be sorted by rank)

        Returns:
            Plain-language recommendation string
        """
        if not quotes:
            return "No quotes available for placement recommendation."

        top_quote = quotes[0]
        return top_quote.scoring.recommendation_rationale or "No recommendation available."

    def _parse_currency(self, value: str) -> float:
        """Parse currency string to float value.

        Args:
            value: Currency string like "$125,000" or "125000"

        Returns:
            Float value (0.0 if parsing fails)
        """
        if not value:
            return 0.0
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r"[$,\s]", "", value)
        try:
            return float(cleaned)
        except ValueError:
            logger.debug(f"Failed to parse currency: {value}")
            return 0.0

    def _calculate_coverage_breadth(self, quote: Quote) -> float:
        """Calculate coverage breadth factor (0.0-1.0).

        More sublimits + fewer exclusions = higher score.

        Args:
            quote: Quote to analyze

        Returns:
            Coverage breadth score 0.0-1.0
        """
        sublimit_count = sum(
            [
                bool(quote.fields.flood_sublimit),
                bool(quote.fields.earthquake_sublimit),
                bool(quote.fields.business_interruption_limit),
            ]
        )
        exclusion_count = len(quote.fields.named_perils_exclusions)

        # More sublimits = better (max 3)
        sublimit_factor = sublimit_count / 3.0
        # Fewer exclusions = better (penalize beyond 3)
        exclusion_penalty = min(exclusion_count * 0.1, 0.5)

        return max(0.0, min(1.0, sublimit_factor - exclusion_penalty))

    def _calculate_coverage_score(self, quote: Quote) -> float:
        """Calculate coverage completeness score (0.0-1.0).

        Args:
            quote: Quote to analyze

        Returns:
            Coverage score 0.0-1.0
        """
        # Count populated sublimit fields
        sublimits = [
            quote.fields.building_limit,
            quote.fields.contents_limit,
            quote.fields.business_interruption_limit,
            quote.fields.flood_sublimit,
            quote.fields.earthquake_sublimit,
        ]
        populated_sublimits = sum(bool(s) for s in sublimits)
        sublimit_score = populated_sublimits / len(sublimits)

        # Penalize for exclusions (more exclusions = lower score)
        exclusion_count = len(quote.fields.named_perils_exclusions)
        exclusion_penalty = min(exclusion_count * 0.08, 0.4)

        return max(0.0, min(1.0, sublimit_score - exclusion_penalty))

    def _calculate_financial_score(
        self, quote: Quote, carrier_profile: CarrierProfile | None
    ) -> float:
        """Calculate carrier financial strength score (0.0-1.0).

        Args:
            quote: Quote with carrier information
            carrier_profile: Optional carrier profile with financials

        Returns:
            Financial strength score 0.0-1.0
        """
        # Start with FSR rating score
        rating = quote.fields.carrier_am_best_rating.strip()
        base_score = self.FSR_SCORES.get(rating, self.UNRATED_SCORE)

        # Apply combined ratio adjustment if profile available
        if carrier_profile and carrier_profile.combined_ratio:
            try:
                combined_ratio = float(
                    carrier_profile.combined_ratio.rstrip("%")
                )
                # Combined ratio < 100% = bonus, > 100% = penalty
                if combined_ratio < 100:
                    ratio_bonus = (100 - combined_ratio) * 0.2
                    base_score = min(100, base_score + ratio_bonus)
                elif combined_ratio > 100:
                    ratio_penalty = (combined_ratio - 100) * 0.15
                    base_score = max(0, base_score - ratio_penalty)
            except (ValueError, AttributeError):
                pass

        return base_score / 100.0

    def _calculate_completeness_score(self, quote: Quote) -> float:
        """Calculate quote completeness score (0.0-1.0).

        Args:
            quote: Quote to analyze

        Returns:
            Completeness score 0.0-1.0
        """
        required_fields = [
            quote.fields.annual_premium,
            quote.fields.total_insured_value,
            quote.fields.building_limit,
            quote.fields.contents_limit,
            quote.fields.deductible,
            quote.fields.policy_period,
            quote.fields.quote_reference_number,
        ]
        populated = sum(bool(f) for f in required_fields)
        return populated / len(required_fields)

    def _determine_coverage_adequacy(self, quote: Quote) -> str:
        """Determine coverage adequacy level.

        Args:
            quote: Quote to analyze

        Returns:
            CoverageAdequacy enum value
        """
        # Check for major sublimits
        has_building = bool(quote.fields.building_limit)
        has_contents = bool(quote.fields.contents_limit)
        has_bi = bool(quote.fields.business_interruption_limit)
        
        major_coverage_count = sum([has_building, has_contents, has_bi])
        
        # Check exclusions
        exclusion_count = len(quote.fields.named_perils_exclusions)
        
        if major_coverage_count >= 3 and exclusion_count <= 2:
            return CoverageAdequacy.ADEQUATE.value
        elif major_coverage_count >= 2 and exclusion_count <= 4:
            return CoverageAdequacy.PARTIAL.value
        else:
            return CoverageAdequacy.INSUFFICIENT.value

    def _identify_coverage_gaps(self, quote: Quote) -> List[str]:
        """Identify specific coverage gaps in the quote.

        Args:
            quote: Quote to analyze

        Returns:
            List of gap descriptions
        """
        gaps = []

        if not quote.fields.flood_sublimit:
            gaps.append("No flood coverage sublimit specified")
        if not quote.fields.earthquake_sublimit:
            gaps.append("No earthquake coverage sublimit specified")
        if not quote.fields.business_interruption_limit:
            gaps.append("No business interruption coverage")

        # Flag significant exclusions
        if len(quote.fields.named_perils_exclusions) > 3:
            gaps.append(
                f"High number of exclusions ({len(quote.fields.named_perils_exclusions)})"
            )

        return gaps

    def _determine_premium_percentile(
        self, premium: float, all_premiums: List[float]
    ) -> str:
        """Determine premium benchmark category.

        Args:
            premium: Premium value for this quote
            all_premiums: List of all valid premiums

        Returns:
            PremiumBenchmark enum value
        """
        if not all_premiums:
            return PremiumBenchmark.MARKET.value

        sorted_premiums = sorted(all_premiums)
        position = sorted_premiums.index(premium) / len(sorted_premiums)

        if position < 0.33:
            return PremiumBenchmark.BELOW_MARKET.value
        elif position > 0.67:
            return PremiumBenchmark.ABOVE_MARKET.value
        else:
            return PremiumBenchmark.MARKET.value

    def _build_rationale(
        self,
        top_quote: Quote,
        all_quotes: List[Quote],
        carrier_profiles: Dict[str, CarrierProfile],
    ) -> str:
        """Build recommendation rationale for top-ranked quote.

        Args:
            top_quote: Top-ranked quote
            all_quotes: All scored quotes
            carrier_profiles: Carrier profile data

        Returns:
            Plain-language rationale string
        """
        reasons = []

        # Premium competitiveness
        premium = self._parse_currency(top_quote.fields.annual_premium)
        if top_quote.scoring.premium_percentile == PremiumBenchmark.BELOW_MARKET.value:
            reasons.append(
                f"Most competitive premium at {top_quote.fields.annual_premium}"
            )

        # Coverage completeness
        if top_quote.scoring.coverage_adequacy == CoverageAdequacy.ADEQUATE.value:
            reasons.append("Comprehensive coverage with minimal exclusions")

        # Financial strength
        if top_quote.fields.carrier_am_best_rating in ["A++", "A+", "A"]:
            reasons.append(
                f"Strong carrier financial rating ({top_quote.fields.carrier_am_best_rating})"
            )

        # Quote quality
        if len(reasons) < 3:
            completeness = self._calculate_completeness_score(top_quote)
            if completeness >= 0.85:
                reasons.append("Complete quote with all key terms specified")

        # Default if no strong reasons
        if not reasons:
            reasons.append(
                f"Highest composite score ({top_quote.scoring.placement_score}/100)"
            )

        # Format top 3 reasons
        top_reasons = reasons[:3]
        rationale = f"Recommended: {top_quote.carrier_name}. "
        rationale += "Key factors: " + "; ".join(top_reasons) + "."

        return rationale
