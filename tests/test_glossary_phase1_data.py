"""
Tests for Phase 1: Glossary Data Layer

Tests cover:
- Glossary JSON structure and validation
- CRUD operations in glossary module
- API endpoints for glossary management
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_glossary_data():
    """Sample glossary data for testing."""
    return {
        "version": "1.0",
        "effective_date": "2026-02-03",
        "last_updated": "2026-02-03",
        "description": "WorkbenchIQ Persona Glossaries",
        "personas": {
            "underwriting": {
                "name": "Life & Health Underwriting",
                "description": "Medical and insurance terminology",
                "categories": [
                    {
                        "id": "general",
                        "name": "General",
                        "terms": [
                            {
                                "abbreviation": "Hx",
                                "meaning": "History",
                                "context": "Medical context",
                                "examples": ["PMHx includes prior surgeries"]
                            },
                            {
                                "abbreviation": "Dx",
                                "meaning": "Diagnosis",
                                "context": "Medical context"
                            }
                        ]
                    },
                    {
                        "id": "cardiac",
                        "name": "Cardiac",
                        "terms": [
                            {
                                "abbreviation": "HTN",
                                "meaning": "Hypertension"
                            },
                            {
                                "abbreviation": "CAD",
                                "meaning": "Coronary artery disease"
                            }
                        ]
                    }
                ]
            },
            "mortgage": {
                "name": "Mortgage Underwriting",
                "description": "Financial and regulatory terminology",
                "categories": [
                    {
                        "id": "ratios",
                        "name": "Ratios",
                        "terms": [
                            {
                                "abbreviation": "GDS",
                                "meaning": "Gross Debt Service (ratio)"
                            },
                            {
                                "abbreviation": "TDS",
                                "meaning": "Total Debt Service (ratio)"
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def temp_glossary(sample_glossary_data):
    """Create a temporary glossary file for testing."""
    temp_dir = tempfile.mkdtemp()
    glossary_path = Path(temp_dir) / "glossary.json"
    
    with open(glossary_path, 'w', encoding='utf-8') as f:
        json.dump(sample_glossary_data, f, indent=2)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from api_server import app
    return TestClient(app)


# ============================================================================
# Test: Glossary JSON Structure
# ============================================================================

class TestGlossaryJSONStructure:
    """Tests for glossary.json file structure."""
    
    def test_glossary_json_exists(self):
        """Verify glossary.json exists in prompts folder."""
        glossary_path = Path("prompts/glossary.json")
        assert glossary_path.exists(), "glossary.json should exist in prompts folder"
    
    def test_glossary_json_valid_json(self):
        """Verify glossary.json is valid JSON."""
        glossary_path = Path("prompts/glossary.json")
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, dict)
    
    def test_glossary_contains_version(self):
        """Verify glossary has version field."""
        glossary_path = Path("prompts/glossary.json")
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert "version" in data
    
    def test_glossary_contains_all_personas(self):
        """Verify all four personas are present."""
        glossary_path = Path("prompts/glossary.json")
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            expected_personas = [
                "underwriting",
                "life_health_claims", 
                "mortgage",
                "automotive_claims"
            ]
            
            for persona in expected_personas:
                assert persona in data.get("personas", {}), \
                    f"Persona '{persona}' should be in glossary"
    
    def test_glossary_term_has_required_fields(self, sample_glossary_data):
        """Verify each term has abbreviation and meaning."""
        for persona_id, persona_data in sample_glossary_data["personas"].items():
            for category in persona_data.get("categories", []):
                for term in category.get("terms", []):
                    assert "abbreviation" in term, \
                        f"Term in {persona_id}/{category['id']} missing abbreviation"
                    assert "meaning" in term, \
                        f"Term in {persona_id}/{category['id']} missing meaning"
    
    def test_glossary_categories_have_unique_ids(self, sample_glossary_data):
        """Verify category IDs are unique within each persona."""
        for persona_id, persona_data in sample_glossary_data["personas"].items():
            category_ids = [c["id"] for c in persona_data.get("categories", [])]
            assert len(category_ids) == len(set(category_ids)), \
                f"Duplicate category IDs in persona '{persona_id}'"
    
    def test_glossary_abbreviations_unique_per_persona(self, sample_glossary_data):
        """Verify abbreviations are unique within each persona."""
        for persona_id, persona_data in sample_glossary_data["personas"].items():
            all_abbrevs = []
            for category in persona_data.get("categories", []):
                for term in category.get("terms", []):
                    all_abbrevs.append(term["abbreviation"])
            
            assert len(all_abbrevs) == len(set(all_abbrevs)), \
                f"Duplicate abbreviations in persona '{persona_id}'"


# ============================================================================
# Test: Glossary Module
# ============================================================================

class TestGlossaryModule:
    """Tests for app/glossary.py module."""
    
    def test_load_glossary(self, temp_glossary):
        """Test loading the full glossary."""
        from app.glossary import load_glossary
        
        data = load_glossary(temp_glossary)
        
        assert "version" in data
        assert "personas" in data
        assert len(data["personas"]) >= 2
    
    def test_get_glossary_for_persona_underwriting(self, temp_glossary):
        """Test getting underwriting glossary."""
        from app.glossary import get_glossary_for_persona
        
        glossary = get_glossary_for_persona(temp_glossary, "underwriting")
        
        assert glossary["name"] == "Life & Health Underwriting"
        assert len(glossary["categories"]) >= 2
    
    def test_get_glossary_for_persona_mortgage(self, temp_glossary):
        """Test getting mortgage glossary."""
        from app.glossary import get_glossary_for_persona
        
        glossary = get_glossary_for_persona(temp_glossary, "mortgage")
        
        assert glossary["name"] == "Mortgage Underwriting"
        assert len(glossary["categories"]) >= 1
    
    def test_get_glossary_for_unknown_persona(self, temp_glossary):
        """Test handling of unknown persona."""
        from app.glossary import get_glossary_for_persona
        
        with pytest.raises(ValueError) as exc_info:
            get_glossary_for_persona(temp_glossary, "unknown_persona")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_search_glossary_exact_match(self, temp_glossary):
        """Test searching with exact abbreviation."""
        from app.glossary import search_glossary
        
        results = search_glossary(temp_glossary, "underwriting", "HTN")
        
        assert len(results) == 1
        assert results[0]["abbreviation"] == "HTN"
        assert results[0]["meaning"] == "Hypertension"
    
    def test_search_glossary_partial_match(self, temp_glossary):
        """Test searching with partial text."""
        from app.glossary import search_glossary
        
        # Search for partial match in meaning
        results = search_glossary(temp_glossary, "underwriting", "History")
        
        assert len(results) >= 1
        assert any(r["abbreviation"] == "Hx" for r in results)
    
    def test_search_glossary_case_insensitive(self, temp_glossary):
        """Test case-insensitive search."""
        from app.glossary import search_glossary
        
        results_upper = search_glossary(temp_glossary, "underwriting", "HTN")
        results_lower = search_glossary(temp_glossary, "underwriting", "htn")
        
        assert len(results_upper) == len(results_lower)
        assert results_upper[0]["abbreviation"] == results_lower[0]["abbreviation"]
    
    def test_search_glossary_by_meaning(self, temp_glossary):
        """Test searching in meaning text."""
        from app.glossary import search_glossary
        
        results = search_glossary(temp_glossary, "underwriting", "Hypertension")
        
        assert len(results) >= 1
        assert results[0]["abbreviation"] == "HTN"
    
    def test_search_glossary_no_results(self, temp_glossary):
        """Test search with no matching results."""
        from app.glossary import search_glossary
        
        results = search_glossary(temp_glossary, "underwriting", "XYZNOTEXIST")
        
        assert len(results) == 0
    
    def test_search_glossary_with_category_filter(self, temp_glossary):
        """Test search filtered by category."""
        from app.glossary import search_glossary
        
        # Search in cardiac category only
        results = search_glossary(
            temp_glossary, "underwriting", "HTN", category="cardiac"
        )
        
        assert len(results) == 1
        assert results[0]["category"] == "cardiac"
    
    def test_add_term_success(self, temp_glossary):
        """Test adding a new term."""
        from app.glossary import add_term, get_glossary_for_persona
        
        new_term = {
            "abbreviation": "MI",
            "meaning": "Myocardial infarction",
            "context": "Cardiac event"
        }
        
        result = add_term(temp_glossary, "underwriting", "cardiac", new_term)
        
        assert result["abbreviation"] == "MI"
        
        # Verify it was saved
        glossary = get_glossary_for_persona(temp_glossary, "underwriting")
        cardiac = next(c for c in glossary["categories"] if c["id"] == "cardiac")
        assert any(t["abbreviation"] == "MI" for t in cardiac["terms"])
    
    def test_add_term_duplicate_raises(self, temp_glossary):
        """Test that duplicate abbreviation raises error."""
        from app.glossary import add_term
        
        duplicate_term = {
            "abbreviation": "HTN",  # Already exists
            "meaning": "Some other meaning"
        }
        
        with pytest.raises(ValueError) as exc_info:
            add_term(temp_glossary, "underwriting", "cardiac", duplicate_term)
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_add_term_invalid_category(self, temp_glossary):
        """Test adding term to non-existent category."""
        from app.glossary import add_term
        
        new_term = {
            "abbreviation": "TEST",
            "meaning": "Test term"
        }
        
        with pytest.raises(ValueError) as exc_info:
            add_term(temp_glossary, "underwriting", "nonexistent", new_term)
        
        assert "category" in str(exc_info.value).lower()
    
    def test_update_term(self, temp_glossary):
        """Test updating an existing term."""
        from app.glossary import update_term, search_glossary
        
        updates = {
            "meaning": "High blood pressure",
            "context": "Updated context"
        }
        
        result = update_term(temp_glossary, "underwriting", "HTN", updates)
        
        assert result["meaning"] == "High blood pressure"
        assert result["context"] == "Updated context"
        
        # Verify it was saved
        results = search_glossary(temp_glossary, "underwriting", "HTN")
        assert results[0]["meaning"] == "High blood pressure"
    
    def test_update_term_not_found(self, temp_glossary):
        """Test updating non-existent term."""
        from app.glossary import update_term
        
        with pytest.raises(ValueError) as exc_info:
            update_term(temp_glossary, "underwriting", "NOTEXIST", {"meaning": "test"})
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_update_term_move_category(self, temp_glossary):
        """Test moving term to different category."""
        from app.glossary import update_term, get_glossary_for_persona
        
        result = update_term(
            temp_glossary, 
            "underwriting", 
            "HTN", 
            {"category_id": "general"}
        )
        
        # Verify it moved
        glossary = get_glossary_for_persona(temp_glossary, "underwriting")
        general = next(c for c in glossary["categories"] if c["id"] == "general")
        cardiac = next(c for c in glossary["categories"] if c["id"] == "cardiac")
        
        assert any(t["abbreviation"] == "HTN" for t in general["terms"])
        assert not any(t["abbreviation"] == "HTN" for t in cardiac["terms"])
    
    def test_delete_term(self, temp_glossary):
        """Test deleting a term."""
        from app.glossary import delete_term, search_glossary
        
        result = delete_term(temp_glossary, "underwriting", "HTN")
        
        assert result is True
        
        # Verify it was deleted
        results = search_glossary(temp_glossary, "underwriting", "HTN")
        assert len(results) == 0
    
    def test_delete_term_not_found(self, temp_glossary):
        """Test deleting non-existent term."""
        from app.glossary import delete_term
        
        with pytest.raises(ValueError) as exc_info:
            delete_term(temp_glossary, "underwriting", "NOTEXIST")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_add_category(self, temp_glossary):
        """Test adding a new category."""
        from app.glossary import add_category, get_glossary_for_persona
        
        new_category = {
            "id": "oncology",
            "name": "Oncology"
        }
        
        result = add_category(temp_glossary, "underwriting", new_category)
        
        assert result["id"] == "oncology"
        assert result["terms"] == []
        
        # Verify it was saved
        glossary = get_glossary_for_persona(temp_glossary, "underwriting")
        assert any(c["id"] == "oncology" for c in glossary["categories"])
    
    def test_add_category_duplicate_raises(self, temp_glossary):
        """Test adding duplicate category raises error."""
        from app.glossary import add_category
        
        duplicate = {
            "id": "cardiac",  # Already exists
            "name": "Another Cardiac"
        }
        
        with pytest.raises(ValueError) as exc_info:
            add_category(temp_glossary, "underwriting", duplicate)
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_delete_category_empty(self, temp_glossary):
        """Test deleting an empty category."""
        from app.glossary import add_category, delete_category, get_glossary_for_persona
        
        # First add an empty category
        add_category(temp_glossary, "underwriting", {"id": "empty_cat", "name": "Empty"})
        
        # Then delete it
        result = delete_category(temp_glossary, "underwriting", "empty_cat")
        
        assert result is True
        
        # Verify it was deleted
        glossary = get_glossary_for_persona(temp_glossary, "underwriting")
        assert not any(c["id"] == "empty_cat" for c in glossary["categories"])
    
    def test_delete_category_not_empty_raises(self, temp_glossary):
        """Test deleting non-empty category raises error."""
        from app.glossary import delete_category
        
        with pytest.raises(ValueError) as exc_info:
            delete_category(temp_glossary, "underwriting", "cardiac")  # Has terms
        
        assert "not empty" in str(exc_info.value).lower()
    
    def test_format_glossary_for_prompt_markdown(self, temp_glossary):
        """Test markdown table formatting."""
        from app.glossary import format_glossary_for_prompt
        
        result = format_glossary_for_prompt(
            temp_glossary, 
            "underwriting",
            format_type="markdown"
        )
        
        assert "| Abbreviation | Meaning |" in result
        assert "HTN" in result
        assert "Hypertension" in result
    
    def test_format_glossary_for_prompt_list(self, temp_glossary):
        """Test list formatting."""
        from app.glossary import format_glossary_for_prompt
        
        result = format_glossary_for_prompt(
            temp_glossary, 
            "underwriting",
            format_type="list"
        )
        
        assert "- HTN: Hypertension" in result or "• HTN: Hypertension" in result
    
    def test_format_glossary_respects_max_terms(self, temp_glossary):
        """Test max_terms limit is respected."""
        from app.glossary import format_glossary_for_prompt
        
        result = format_glossary_for_prompt(
            temp_glossary, 
            "underwriting",
            max_terms=2
        )
        
        # Count number of abbreviation entries (excluding header)
        lines = result.strip().split('\n')
        term_lines = [l for l in lines if '|' in l and 'Abbreviation' not in l and '---' not in l]
        
        assert len(term_lines) <= 2
    
    def test_format_glossary_category_filter(self, temp_glossary):
        """Test filtering by specific categories."""
        from app.glossary import format_glossary_for_prompt
        
        result = format_glossary_for_prompt(
            temp_glossary, 
            "underwriting",
            categories=["cardiac"]
        )
        
        assert "HTN" in result
        assert "Hx" not in result  # Hx is in "general" category


# ============================================================================
# Test: Glossary API Endpoints
# ============================================================================

class TestGlossaryAPI:
    """Tests for glossary API endpoints."""
    
    def test_api_list_glossaries(self, client):
        """Test GET /api/glossary returns all personas."""
        response = client.get("/api/glossary")
        
        assert response.status_code == 200
        data = response.json()
        assert "glossaries" in data
        assert len(data["glossaries"]) >= 4
    
    def test_api_get_glossary_for_persona(self, client):
        """Test GET /api/glossary/{persona}."""
        response = client.get("/api/glossary/underwriting")
        
        assert response.status_code == 200
        data = response.json()
        assert data["persona"] == "underwriting"
        assert "categories" in data
        assert "total_terms" in data
    
    def test_api_get_glossary_not_found(self, client):
        """Test 404 for unknown persona."""
        response = client.get("/api/glossary/unknown_persona")
        
        assert response.status_code == 404
    
    def test_api_search_glossary(self, client):
        """Test search endpoint with query."""
        response = client.get("/api/glossary/underwriting/search?q=HTN")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) >= 1
    
    def test_api_search_glossary_with_category(self, client):
        """Test search with category filter."""
        response = client.get(
            "/api/glossary/underwriting/search?q=HTN&category=cardiac"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(r.get("category") == "cardiac" for r in data["results"])
    
    def test_api_search_glossary_no_results(self, client):
        """Test search with no matching results."""
        response = client.get("/api/glossary/underwriting/search?q=XYZNOTEXIST")
        
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_add_term(self, client):
        """Test POST term endpoint."""
        term_data = {
            "category_id": "cardiac",
            "abbreviation": "PCI",
            "meaning": "Percutaneous Coronary Intervention"
        }
        
        response = client.post(
            "/api/glossary/underwriting/terms",
            json=term_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["abbreviation"] == "PCI"
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_add_term_duplicate(self, client):
        """Test 409 for duplicate term."""
        term_data = {
            "category_id": "cardiac",
            "abbreviation": "HTN",  # Already exists
            "meaning": "Duplicate"
        }
        
        response = client.post(
            "/api/glossary/underwriting/terms",
            json=term_data
        )
        
        assert response.status_code == 409
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_add_term_invalid_category(self, client):
        """Test 404 for invalid category."""
        term_data = {
            "category_id": "nonexistent",
            "abbreviation": "TEST",
            "meaning": "Test"
        }
        
        response = client.post(
            "/api/glossary/underwriting/terms",
            json=term_data
        )
        
        assert response.status_code == 404
    
    def test_api_add_term_missing_required(self, client):
        """Test 422 for missing required fields."""
        term_data = {
            "category_id": "cardiac"
            # Missing abbreviation and meaning
        }
        
        response = client.post(
            "/api/glossary/underwriting/terms",
            json=term_data
        )
        
        assert response.status_code == 422
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_update_term(self, client):
        """Test PUT term endpoint."""
        update_data = {
            "meaning": "Updated meaning"
        }
        
        response = client.put(
            "/api/glossary/underwriting/terms/HTN",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["meaning"] == "Updated meaning"
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_delete_term(self, client):
        """Test DELETE term endpoint."""
        # First add a term to delete
        client.post(
            "/api/glossary/underwriting/terms",
            json={
                "category_id": "cardiac",
                "abbreviation": "TODELETE",
                "meaning": "To be deleted"
            }
        )
        
        response = client.delete("/api/glossary/underwriting/terms/TODELETE")
        
        assert response.status_code == 200
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_add_category(self, client):
        """Test POST category endpoint."""
        category_data = {
            "id": "new_category",
            "name": "New Category"
        }
        
        response = client.post(
            "/api/glossary/underwriting/categories",
            json=category_data
        )
        
        assert response.status_code == 201
    
    @pytest.mark.skip(reason="Requires writable test glossary")
    def test_api_delete_category_not_empty(self, client):
        """Test 409 when deleting non-empty category."""
        response = client.delete("/api/glossary/underwriting/categories/cardiac")
        
        assert response.status_code == 409


# ============================================================================
# Test: Integration
# ============================================================================

class TestGlossaryIntegration:
    """Integration tests for glossary functionality."""
    
    def test_full_crud_workflow(self, temp_glossary):
        """Test complete create-read-update-delete workflow."""
        from app.glossary import (
            add_category,
            add_term,
            update_term,
            delete_term,
            delete_category,
            search_glossary
        )
        
        # Create category
        add_category(temp_glossary, "underwriting", {"id": "test_cat", "name": "Test"})
        
        # Add term
        add_term(temp_glossary, "underwriting", "test_cat", {
            "abbreviation": "TEST",
            "meaning": "Test term"
        })
        
        # Search for it
        results = search_glossary(temp_glossary, "underwriting", "TEST")
        assert len(results) == 1
        
        # Update it
        update_term(temp_glossary, "underwriting", "TEST", {"meaning": "Updated"})
        results = search_glossary(temp_glossary, "underwriting", "TEST")
        assert results[0]["meaning"] == "Updated"
        
        # Delete term
        delete_term(temp_glossary, "underwriting", "TEST")
        results = search_glossary(temp_glossary, "underwriting", "TEST")
        assert len(results) == 0
        
        # Delete category
        delete_category(temp_glossary, "underwriting", "test_cat")
    
    def test_glossary_persistence(self, temp_glossary):
        """Test that changes persist across module reloads."""
        from app.glossary import add_term, load_glossary
        
        # Add a term
        add_term(temp_glossary, "underwriting", "cardiac", {
            "abbreviation": "PERSIST",
            "meaning": "Persistence test"
        })
        
        # Reload glossary (simulating module reload)
        data = load_glossary(temp_glossary)
        
        # Find the term
        cardiac = None
        for cat in data["personas"]["underwriting"]["categories"]:
            if cat["id"] == "cardiac":
                cardiac = cat
                break
        
        assert cardiac is not None
        assert any(t["abbreviation"] == "PERSIST" for t in cardiac["terms"])
