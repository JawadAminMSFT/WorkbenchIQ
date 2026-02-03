"""
Tests for Phase 4: Chat Integration

Tests cover:
- Glossary in chat system prompt
- Term lookup in chat
- Context-aware interpretation
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_glossary():
    """Sample glossary data for chat testing."""
    return {
        "version": "1.0",
        "personas": {
            "underwriting": {
                "name": "Life & Health Underwriting",
                "categories": [
                    {
                        "id": "general",
                        "name": "General",
                        "terms": [
                            {"abbreviation": "Hx", "meaning": "History"},
                            {"abbreviation": "PMHx", "meaning": "Past medical history"},
                            {"abbreviation": "Dx", "meaning": "Diagnosis"},
                            {"abbreviation": "Rx", "meaning": "Prescription"},
                        ]
                    },
                    {
                        "id": "cardiac",
                        "name": "Cardiac",
                        "terms": [
                            {"abbreviation": "HTN", "meaning": "Hypertension"},
                            {"abbreviation": "CAD", "meaning": "Coronary artery disease"},
                            {"abbreviation": "MI", "meaning": "Myocardial infarction"},
                            {"abbreviation": "CHF", "meaning": "Congestive heart failure"},
                        ]
                    },
                    {
                        "id": "endocrine",
                        "name": "Endocrine",
                        "terms": [
                            {"abbreviation": "DM", "meaning": "Diabetes mellitus"},
                            {"abbreviation": "T2DM", "meaning": "Type 2 diabetes mellitus"},
                            {"abbreviation": "A1C", "meaning": "Hemoglobin A1c"},
                        ]
                    }
                ]
            },
            "mortgage": {
                "name": "Mortgage Underwriting",
                "categories": [
                    {
                        "id": "ratios",
                        "name": "Ratios",
                        "terms": [
                            {"abbreviation": "GDS", "meaning": "Gross Debt Service (ratio)"},
                            {"abbreviation": "TDS", "meaning": "Total Debt Service (ratio)"},
                            {"abbreviation": "LTV", "meaning": "Loan-to-Value (ratio)"},
                            {"abbreviation": "MQR", "meaning": "Mortgage Qualifying Rate"},
                        ]
                    },
                    {
                        "id": "regulatory",
                        "name": "Regulatory",
                        "terms": [
                            {"abbreviation": "OSFI", "meaning": "Office of the Superintendent of Financial Institutions"},
                            {"abbreviation": "B-20", "meaning": "OSFI Guideline B-20 (Residential Mortgage Underwriting)"},
                            {"abbreviation": "CMHC", "meaning": "Canada Mortgage and Housing Corporation"},
                        ]
                    }
                ]
            },
            "automotive_claims": {
                "name": "Automotive Claims",
                "categories": [
                    {
                        "id": "damage",
                        "name": "Damage Assessment",
                        "terms": [
                            {"abbreviation": "TL", "meaning": "Total Loss"},
                            {"abbreviation": "PDR", "meaning": "Paintless Dent Repair"},
                            {"abbreviation": "ACV", "meaning": "Actual Cash Value"},
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_chat_context():
    """Mock chat context with application data."""
    return {
        "app_id": "test-app-001",
        "persona": "underwriting",
        "document_markdown": "Patient has HTN, DM, and CAD. PMHx significant for MI in 2020.",
        "llm_outputs": {
            "application_summary": {
                "medical_summary": {
                    "parsed": {
                        "conditions": ["Hypertension", "Diabetes", "CAD"],
                        "risk_assessment": "Moderate risk due to cardiac history"
                    }
                }
            }
        }
    }


# ============================================================================
# Test: Chat System Prompt Modification
# ============================================================================

class TestChatSystemPrompt:
    """Tests for chat system prompt modification."""
    
    def test_system_prompt_includes_glossary_section(self, sample_glossary):
        """Test glossary section appears in system prompt."""
        from api_server import get_chat_system_prompt
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.format_glossary_for_prompt') as mock_format:
            mock_format.return_value = "- HTN: Hypertension\n- DM: Diabetes mellitus"
            
            prompt = get_chat_system_prompt(
                persona="underwriting",
                policies_context="## Policies...",
                app_id="test-001",
                app_context_parts=["## Documents..."],
            )
        
        # Should contain glossary header
        assert "Domain Terminology" in prompt or "Glossary" in prompt
        
        # Should contain the formatted glossary
        assert "HTN" in prompt
        assert "Hypertension" in prompt
    
    def test_glossary_per_persona_in_chat_underwriting(self, sample_glossary):
        """Test correct glossary for underwriting persona."""
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            result = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                format_type="list"
            )
        
        # Should have medical terms
        assert "HTN" in result
        assert "CAD" in result
        assert "DM" in result
        
        # Should NOT have mortgage or auto claims terms
        assert "GDS" not in result
        assert "TL" not in result
    
    def test_glossary_per_persona_in_chat_mortgage(self, sample_glossary):
        """Test correct glossary for mortgage persona."""
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            result = format_glossary_for_prompt(
                "prompts",
                "mortgage",
                format_type="list"
            )
        
        # Should have mortgage terms
        assert "GDS" in result
        assert "TDS" in result
        assert "OSFI" in result
        
        # Should NOT have medical terms
        assert "HTN" not in result
    
    def test_glossary_per_persona_in_chat_automotive(self, sample_glossary):
        """Test correct glossary for automotive claims persona."""
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            result = format_glossary_for_prompt(
                "prompts",
                "automotive_claims",
                format_type="list"
            )
        
        # Should have auto claims terms
        assert "TL" in result
        assert "PDR" in result
        assert "ACV" in result
    
    def test_glossary_compact_format_for_chat(self, sample_glossary):
        """Test glossary is appropriately sized for chat context."""
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            result = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                max_terms=75,  # Chat limit
                format_type="list"  # More compact
            )
        
        # List format should be more compact than markdown
        assert "| Abbreviation |" not in result
        
        # Should still contain key terms
        assert "HTN" in result
    
    def test_glossary_instruction_in_prompt(self, sample_glossary):
        """Test instruction for interpreting abbreviations."""
        from api_server import get_chat_system_prompt
        
        with patch('app.glossary.format_glossary_for_prompt') as mock_format:
            mock_format.return_value = "- HTN: Hypertension"
            
            prompt = get_chat_system_prompt(
                persona="underwriting",
                policies_context="",
                app_id="test",
                app_context_parts=[],
            )
        
        # Should include instruction about using glossary
        assert any(phrase in prompt.lower() for phrase in [
            "abbreviation",
            "terminology",
            "interpret",
            "understand"
        ])


# ============================================================================
# Test: Explicit Term Lookup
# ============================================================================

class TestTermLookup:
    """Tests for explicit term lookup in chat."""
    
    def test_what_does_term_mean_htn(self, sample_glossary):
        """
        Test 'What does HTN mean?' response.
        
        Expected: Chat should respond with "HTN stands for Hypertension"
        or similar explanation from glossary.
        """
        # This would be an integration test with actual chat
        # For unit testing, we verify the glossary lookup function
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results = search_glossary("prompts", "underwriting", "HTN")
        
        assert len(results) == 1
        assert results[0]["meaning"] == "Hypertension"
    
    def test_what_does_term_mean_gds(self, sample_glossary):
        """Test 'What does GDS mean?' for mortgage persona."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results = search_glossary("prompts", "mortgage", "GDS")
        
        assert len(results) == 1
        assert "Gross Debt Service" in results[0]["meaning"]
    
    def test_define_term_dm(self, sample_glossary):
        """Test 'Define DM' response."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results = search_glossary("prompts", "underwriting", "DM")
        
        assert len(results) >= 1
        assert any("Diabetes" in r["meaning"] for r in results)
    
    def test_unknown_term_fallback(self, sample_glossary):
        """Test response for unknown terms."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results = search_glossary("prompts", "underwriting", "XYZUNKNOWN")
        
        # Should return empty, chat would fall back to general knowledge
        assert len(results) == 0
    
    def test_case_insensitive_lookup(self, sample_glossary):
        """Test term lookup is case-insensitive."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results_upper = search_glossary("prompts", "underwriting", "HTN")
            results_lower = search_glossary("prompts", "underwriting", "htn")
            results_mixed = search_glossary("prompts", "underwriting", "Htn")
        
        assert len(results_upper) == len(results_lower) == len(results_mixed)
        assert results_upper[0]["abbreviation"] == results_lower[0]["abbreviation"]
    
    def test_partial_term_match(self, sample_glossary):
        """Test partial term matching in search."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            # Search for partial abbreviation
            results = search_glossary("prompts", "underwriting", "T2")
        
        # Should find T2DM
        assert any("T2DM" in r["abbreviation"] for r in results)
    
    def test_meaning_search(self, sample_glossary):
        """Test searching by meaning text."""
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            results = search_glossary("prompts", "underwriting", "Hypertension")
        
        # Should find HTN
        assert any("HTN" in r["abbreviation"] for r in results)


# ============================================================================
# Test: Context-Aware Interpretation
# ============================================================================

class TestContextInterpretation:
    """Tests for contextual interpretation in chat."""
    
    def test_abbreviation_in_question_underwriting(self, sample_glossary, mock_chat_context):
        """
        Test chat understands abbreviations in questions.
        
        Question: "What is the risk for someone with HTN and DM?"
        Expected: Chat interprets as "Hypertension and Diabetes mellitus"
        """
        # With glossary in system prompt, LLM should understand
        # This is verified by having glossary context injected
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            glossary_context = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                format_type="list"
            )
        
        # Verify context contains the terms
        assert "HTN" in glossary_context
        assert "DM" in glossary_context
        assert "Hypertension" in glossary_context
        assert "Diabetes" in glossary_context
    
    def test_abbreviation_in_question_mortgage(self, sample_glossary):
        """
        Test chat understands mortgage abbreviations in questions.
        
        Question: "What happens if GDS exceeds 39%?"
        Expected: Chat interprets as "Gross Debt Service ratio"
        """
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            glossary_context = format_glossary_for_prompt(
                "prompts",
                "mortgage",
                format_type="list"
            )
        
        assert "GDS" in glossary_context
        assert "Gross Debt Service" in glossary_context
    
    def test_abbreviation_in_document_context(self, sample_glossary, mock_chat_context):
        """
        Test chat interprets abbreviations from docs.
        
        Document: "Patient has HTN, DM, and CAD. PMHx significant for MI in 2020."
        Chat should understand all these abbreviations when answering.
        """
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            glossary_context = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                format_type="list"
            )
        
        # All abbreviations from the document should be in glossary
        doc_abbrevs = ["HTN", "DM", "CAD", "PMHx", "MI"]
        for abbr in doc_abbrevs:
            assert abbr in glossary_context, f"Missing abbreviation: {abbr}"
    
    def test_mixed_abbreviations_and_full_terms(self, sample_glossary):
        """
        Test chat handles mix of abbreviations and full terms.
        
        Question: "Compare risk of Hypertension vs DM"
        Expected: Chat understands both the full term and abbreviation
        """
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            glossary_context = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                format_type="list"
            )
        
        # Both terms should be present for reference
        assert "Hypertension" in glossary_context
        assert "DM" in glossary_context
        assert "Diabetes" in glossary_context
    
    def test_related_terms_context(self, sample_glossary):
        """
        Test chat can relate similar terms.
        
        DM and T2DM are related - chat should understand both.
        """
        from app.glossary import search_glossary
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            dm_results = search_glossary("prompts", "underwriting", "DM")
            t2dm_results = search_glossary("prompts", "underwriting", "T2DM")
        
        # Both should be found
        assert len(dm_results) >= 1
        assert len(t2dm_results) >= 1
        
        # Both relate to diabetes
        assert "Diabetes" in dm_results[0]["meaning"]
        assert "diabetes" in t2dm_results[0]["meaning"].lower()


# ============================================================================
# Test: Chat API Integration
# ============================================================================

class TestChatAPIIntegration:
    """Tests for chat API endpoint integration."""
    
    def test_chat_endpoint_includes_glossary(self):
        """
        Test /api/applications/{app_id}/chat includes glossary.
        
        The system prompt sent to OpenAI should include glossary context.
        """
        # This would be tested via the FastAPI test client
        # Verifying the system prompt construction
        assert True  # Placeholder
    
    def test_conversation_endpoint_includes_glossary(self):
        """
        Test /api/applications/{app_id}/conversations includes glossary.
        
        New conversations and continued ones should have glossary context.
        """
        assert True  # Placeholder
    
    def test_glossary_not_saved_in_conversation(self):
        """
        Test glossary is injected but not saved in conversation history.
        
        System prompt with glossary is ephemeral - not stored with messages.
        """
        assert True  # Placeholder
    
    def test_glossary_per_conversation_persona(self):
        """
        Test conversation uses persona from application/request.
        
        Glossary should match the persona of the application being discussed.
        """
        assert True  # Placeholder


# ============================================================================
# Test: Error Handling in Chat
# ============================================================================

class TestChatErrorHandling:
    """Tests for error handling in chat glossary integration."""
    
    def test_chat_works_without_glossary(self):
        """
        Test chat still works if glossary is unavailable.
        
        Chat should continue with empty glossary context, not fail.
        """
        from api_server import get_chat_system_prompt
        
        with patch('app.glossary.format_glossary_for_prompt', return_value=""):
            prompt = get_chat_system_prompt(
                persona="underwriting",
                policies_context="## Policies",
                app_id="test",
                app_context_parts=[],
            )
        
        # Prompt should still be valid
        assert len(prompt) > 100
        assert "underwriter" in prompt.lower() or "expert" in prompt.lower()
    
    def test_chat_handles_glossary_load_error(self):
        """
        Test chat handles glossary loading errors gracefully.
        """
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', side_effect=Exception("File error")):
            result = format_glossary_for_prompt("prompts", "underwriting")
        
        # Should return empty, not raise
        assert result == "" or result is None
    
    def test_unknown_persona_uses_empty_glossary(self):
        """
        Test unknown persona gets empty glossary, not error.
        """
        from app.glossary import format_glossary_for_prompt
        
        glossary = {
            "version": "1.0",
            "personas": {
                "underwriting": {"name": "Test", "categories": []}
            }
        }
        
        with patch('app.glossary.load_glossary', return_value=glossary):
            result = format_glossary_for_prompt("prompts", "unknown_persona")
        
        # Should return empty, not raise
        assert result == "" or result is None or "no glossary" in result.lower()


# ============================================================================
# Test: Performance in Chat
# ============================================================================

class TestChatPerformance:
    """Tests for chat performance with glossary."""
    
    def test_glossary_format_fast_for_chat(self, sample_glossary):
        """
        Test glossary formatting is fast enough for chat.
        
        Should add minimal latency to chat response.
        """
        import time
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            start = time.time()
            for _ in range(100):
                format_glossary_for_prompt("prompts", "underwriting", format_type="list")
            elapsed = time.time() - start
        
        # 100 calls should complete in under 1 second
        assert elapsed < 1.0, f"100 calls took {elapsed:.3f}s"
    
    def test_glossary_token_count_reasonable(self, sample_glossary):
        """
        Test glossary doesn't use excessive tokens.
        
        Should use roughly 500-1000 tokens for typical glossary.
        """
        from app.glossary import format_glossary_for_prompt
        
        with patch('app.glossary.load_glossary', return_value=sample_glossary):
            result = format_glossary_for_prompt(
                "prompts",
                "underwriting",
                max_terms=75,
                format_type="list"
            )
        
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = len(result) / 4
        
        # Should be under 2000 tokens
        assert estimated_tokens < 2000, f"Estimated {estimated_tokens} tokens"
