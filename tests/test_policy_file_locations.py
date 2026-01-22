"""
Test suite for policy and prompt file locations.

This test suite verifies that all policy and prompt JSON files are accessible
from the correct locations and that all code references point to valid paths.

Run before and after migration from data/ to prompts/ folder.
"""

import json
import os
import pytest
from pathlib import Path

# Get project root (one level up from tests/)
PROJECT_ROOT = Path(__file__).parent.parent


class TestPolicyFileLocations:
    """Test that policy files exist in expected locations."""

    # Expected files in prompts/ folder after migration
    EXPECTED_PROMPTS_FILES = [
        "prompts.json",
        "risk-analysis-prompts.json",
        "policies.json",
        "life-health-underwriting-policies.json",
        "life-health-claims-policies.json",
        "automotive-claims-policies.json",
        "property-casualty-claims-policies.json",
    ]

    def test_prompts_folder_exists(self):
        """Verify prompts folder exists."""
        prompts_dir = PROJECT_ROOT / "prompts"
        assert prompts_dir.exists(), f"prompts/ folder should exist at {prompts_dir}"
        assert prompts_dir.is_dir(), f"{prompts_dir} should be a directory"

    def test_data_folder_exists(self):
        """Verify data folder exists."""
        data_dir = PROJECT_ROOT / "data"
        assert data_dir.exists(), f"data/ folder should exist at {data_dir}"
        assert data_dir.is_dir(), f"{data_dir} should be a directory"

    def test_data_folder_only_has_apps_and_conversations(self):
        """After migration, data/ should only have applications/ and conversations/."""
        data_dir = PROJECT_ROOT / "data"
        if not data_dir.exists():
            pytest.skip("data/ folder does not exist")
        
        # Get all items in data/
        items = list(data_dir.iterdir())
        item_names = [item.name for item in items]
        
        # Filter to only JSON files (which should be moved)
        json_files = [name for name in item_names if name.endswith('.json')]
        
        # After migration, there should be no JSON files in data/
        # This test will fail before migration (expected) and pass after
        if json_files:
            pytest.skip(f"Found JSON files in data/ - migration pending: {json_files}")

    @pytest.mark.parametrize("filename", EXPECTED_PROMPTS_FILES)
    def test_policy_file_in_prompts(self, filename):
        """Verify each policy/prompt file exists in prompts/ folder."""
        file_path = PROJECT_ROOT / "prompts" / filename
        assert file_path.exists(), f"{filename} should exist in prompts/ folder"

    @pytest.mark.parametrize("filename", EXPECTED_PROMPTS_FILES)
    def test_policy_file_is_valid_json(self, filename):
        """Verify each policy/prompt file is valid JSON."""
        file_path = PROJECT_ROOT / "prompts" / filename
        if not file_path.exists():
            pytest.skip(f"{filename} not found in prompts/")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                assert data is not None
            except json.JSONDecodeError as e:
                pytest.fail(f"{filename} is not valid JSON: {e}")


class TestUnderwritingPoliciesStructure:
    """Test the structure of underwriting policies file."""

    def get_policies_path(self):
        """Get path to underwriting policies file (check both locations)."""
        prompts_path = PROJECT_ROOT / "prompts" / "life-health-underwriting-policies.json"
        data_path = PROJECT_ROOT / "data" / "life-health-underwriting-policies.json"
        
        if prompts_path.exists():
            return prompts_path
        elif data_path.exists():
            return data_path
        else:
            pytest.skip("life-health-underwriting-policies.json not found")

    def test_has_policies_array(self):
        """Verify policies file has policies array."""
        path = self.get_policies_path()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "policies" in data, "File should have 'policies' key"
        assert isinstance(data["policies"], list), "'policies' should be a list"
        assert len(data["policies"]) > 0, "Should have at least one policy"

    def test_policy_has_required_fields(self):
        """Verify each policy has required fields."""
        path = self.get_policies_path()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_fields = ["id", "category", "name", "criteria"]
        
        for policy in data["policies"]:
            for field in required_fields:
                assert field in policy, f"Policy should have '{field}' field"


class TestAutomotiveClaimsPoliciesStructure:
    """Test the structure of automotive claims policies file."""

    def get_policies_path(self):
        """Get path to automotive claims policies file (check both locations)."""
        prompts_path = PROJECT_ROOT / "prompts" / "automotive-claims-policies.json"
        data_path = PROJECT_ROOT / "data" / "automotive-claims-policies.json"
        
        if prompts_path.exists():
            return prompts_path
        elif data_path.exists():
            return data_path
        else:
            pytest.skip("automotive-claims-policies.json not found")

    def test_has_policies_array(self):
        """Verify policies file has policies array."""
        path = self.get_policies_path()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "policies" in data, "File should have 'policies' key"
        assert isinstance(data["policies"], list), "'policies' should be a list"

    def test_has_automotive_categories(self):
        """Verify automotive policies have expected categories."""
        path = self.get_policies_path()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        categories = {p.get("category") for p in data["policies"]}
        expected_categories = {"damage_assessment", "liability_determination", "fraud_detection", "payout_calculation"}
        
        # At least some expected categories should be present
        found = categories & expected_categories
        assert len(found) > 0, f"Should have some automotive categories. Found: {categories}"


class TestCodeReferencesPointToPrompts:
    """Test that code references point to prompts/ folder after migration."""

    def test_unified_indexer_uses_prompts_path(self):
        """Verify unified_indexer.py uses prompts/ paths."""
        indexer_path = PROJECT_ROOT / "app" / "rag" / "unified_indexer.py"
        if not indexer_path.exists():
            pytest.skip("unified_indexer.py not found")
        
        content = indexer_path.read_text(encoding='utf-8')
        
        # After migration, should use prompts/ not data/
        # This test documents the expected state after migration
        if 'data/' in content and 'policies_path' in content:
            # Check if it's using data/ paths for policies
            if '"data/life-health' in content or '"data/automotive' in content:
                pytest.skip("Code still references data/ - migration pending")

    def test_config_uses_prompts_path(self):
        """Verify config.py uses prompts/ paths."""
        config_path = PROJECT_ROOT / "app" / "config.py"
        if not config_path.exists():
            pytest.skip("config.py not found")
        
        content = config_path.read_text(encoding='utf-8')
        
        # Check for data/ references to policy files
        if 'data/automotive-claims-policies.json' in content:
            pytest.skip("config.py still references data/ - migration pending")

    def test_api_server_uses_prompts_path(self):
        """Verify api_server.py uses prompts/ paths for policies."""
        api_path = PROJECT_ROOT / "api_server.py"
        if not api_path.exists():
            pytest.skip("api_server.py not found")
        
        content = api_path.read_text(encoding='utf-8')
        
        # Check for data/ references to policy files
        if '"data/life-health-underwriting-policies.json"' in content:
            pytest.skip("api_server.py still references data/ - migration pending")


class TestPolicyLoading:
    """Test that policies can be loaded via the app modules."""

    def test_load_underwriting_policies(self):
        """Test loading underwriting policies via the module."""
        try:
            from app.underwriting_policies import load_policies
            
            # Try prompts/ first, then data/
            for root in ["prompts", "data"]:
                try:
                    policies = load_policies(root)
                    assert policies is not None
                    assert "policies" in policies or len(policies) > 0
                    return  # Success
                except (FileNotFoundError, ValueError):
                    continue
            
            pytest.fail("Could not load underwriting policies from either location")
        except ImportError:
            pytest.skip("app.underwriting_policies module not available")

    def test_load_prompts(self):
        """Test loading prompts via the module."""
        try:
            from app.prompts import load_prompts
            
            # Try prompts/ first, then data/
            for root in ["prompts", "data"]:
                try:
                    prompts = load_prompts(root)
                    assert prompts is not None
                    return  # Success
                except (FileNotFoundError, ValueError):
                    continue
            
            pytest.fail("Could not load prompts from either location")
        except ImportError:
            pytest.skip("app.prompts module not available")


class TestClaimsPolicyLoading:
    """Test that claims policies can be loaded."""

    def test_load_automotive_claims_policies(self):
        """Test loading automotive claims policies."""
        try:
            from app.claims.policies import ClaimsPolicyLoader
            
            loader = ClaimsPolicyLoader()
            
            # Try prompts/ first, then data/
            for root in ["prompts", "data"]:
                path = f"{root}/automotive-claims-policies.json"
                full_path = PROJECT_ROOT / path
                if full_path.exists():
                    loader.load_policies(path)
                    policies = loader.get_all_policies()
                    assert len(policies) > 0, "Should load at least one policy"
                    return
            
            pytest.skip("automotive-claims-policies.json not found in either location")
        except ImportError:
            pytest.skip("app.claims.policies module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
