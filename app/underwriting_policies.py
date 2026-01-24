"""
Underwriting Policy Management for WorkbenchIQ.

This module handles loading, validating, and formatting underwriting policies
for injection into LLM prompts. Policies are defined in JSON files and used
to ensure consistent, auditable risk assessments with proper citations.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .utils import setup_logging

logger = setup_logging()


# Cache for loaded policies
_policy_cache: Dict[str, Dict[str, Any]] = {}


@dataclass
class PolicyCriteria:
    """A single criteria within an underwriting policy."""
    id: str
    condition: str
    risk_level: str
    action: str
    rationale: str


@dataclass
class UnderwritingPolicy:
    """An underwriting policy with its criteria and modifying factors."""
    id: str
    category: str
    subcategory: str
    name: str
    description: str
    criteria: List[PolicyCriteria]
    modifying_factors: List[Dict[str, str]]
    references: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnderwritingPolicy":
        """Create an UnderwritingPolicy from a dictionary."""
        criteria = [
            PolicyCriteria(
                id=c["id"],
                condition=c["condition"],
                risk_level=c["risk_level"],
                action=c["action"],
                rationale=c["rationale"],
            )
            for c in data.get("criteria", [])
        ]
        return cls(
            id=data["id"],
            category=data["category"],
            subcategory=data["subcategory"],
            name=data["name"],
            description=data["description"],
            criteria=criteria,
            modifying_factors=data.get("modifying_factors", []),
            references=data.get("references", []),
        )


def _get_policy_file_path(storage_root: str) -> str:
    """Get the path to the underwriting policies file."""
    return os.path.join(storage_root, "life-health-underwriting-policies.json")


def load_policies(storage_root: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Load underwriting policies from the JSON file.
    
    Args:
        storage_root: Path to the data storage directory (e.g., "data/")
        use_cache: Whether to use cached policies if available
        
    Returns:
        Dictionary containing the full policies structure
    """
    cache_key = storage_root
    
    if use_cache and cache_key in _policy_cache:
        return _policy_cache[cache_key]
    
    policy_file = _get_policy_file_path(storage_root)
    
    try:
        if os.path.exists(policy_file):
            with open(policy_file, 'r', encoding='utf-8') as f:
                policies = json.load(f)
                
            # Validate basic structure
            if "policies" not in policies or not isinstance(policies["policies"], list):
                logger.warning("Invalid policy file structure. Expected 'policies' array.")
                return _get_empty_policies()
            
            logger.info(
                "Loaded %d underwriting policies from %s",
                len(policies["policies"]),
                policy_file
            )
            
            if use_cache:
                _policy_cache[cache_key] = policies
                
            return policies
        else:
            logger.warning("Underwriting policies file not found: %s", policy_file)
            return _get_empty_policies()
            
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load underwriting policies: %s", str(e))
        return _get_empty_policies()


def _get_empty_policies() -> Dict[str, Any]:
    """Return an empty policies structure."""
    return {
        "version": "1.0",
        "policies": [],
    }


def save_policies(storage_root: str, policies_data: Dict[str, Any]) -> bool:
    """
    Save underwriting policies to the JSON file.
    
    Args:
        storage_root: Path to the prompts directory
        policies_data: Full policies data structure with 'version' and 'policies' keys
        
    Returns:
        True if save was successful, False otherwise
    """
    policy_file = _get_policy_file_path(storage_root)
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(policy_file), exist_ok=True)
        
        with open(policy_file, 'w', encoding='utf-8') as f:
            json.dump(policies_data, f, indent=2)
        
        # Clear cache after save
        clear_policy_cache()
        
        logger.info("Saved %d policies to %s", len(policies_data.get("policies", [])), policy_file)
        return True
        
    except (IOError, OSError) as e:
        logger.error("Failed to save policies: %s", str(e))
        return False


def add_policy(storage_root: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new policy.
    
    Args:
        storage_root: Path to the prompts directory
        policy: Policy dictionary to add
        
    Returns:
        Result dictionary with success status and policy
        
    Raises:
        ValueError: If policy with same ID already exists
    """
    policies_data = load_policies(storage_root, use_cache=False)
    
    # Check if policy with same ID exists
    existing_ids = [p.get("id") for p in policies_data.get("policies", [])]
    if policy.get("id") in existing_ids:
        raise ValueError(f"Policy with ID '{policy.get('id')}' already exists")
    
    policies_data["policies"].append(policy)
    
    if save_policies(storage_root, policies_data):
        return {"success": True, "policy": policy}
    else:
        raise IOError("Failed to save policy")


def update_policy(storage_root: str, policy_id: str, policy_update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing policy.
    
    Args:
        storage_root: Path to the prompts directory
        policy_id: ID of the policy to update
        policy_update: Updated policy data
        
    Returns:
        Result dictionary with success status and updated policy
        
    Raises:
        ValueError: If policy not found
    """
    policies_data = load_policies(storage_root, use_cache=False)
    
    policy_index = None
    for i, p in enumerate(policies_data.get("policies", [])):
        if p.get("id") == policy_id:
            policy_index = i
            break
    
    if policy_index is None:
        raise ValueError(f"Policy '{policy_id}' not found")
    
    # Merge update with existing policy, preserving ID
    updated_policy = {**policies_data["policies"][policy_index], **policy_update}
    updated_policy["id"] = policy_id  # Ensure ID is preserved
    policies_data["policies"][policy_index] = updated_policy
    
    if save_policies(storage_root, policies_data):
        return {"success": True, "policy": updated_policy}
    else:
        raise IOError("Failed to save policy")


def delete_policy(storage_root: str, policy_id: str) -> Dict[str, Any]:
    """
    Delete a policy by ID.
    
    Args:
        storage_root: Path to the prompts directory
        policy_id: ID of the policy to delete
        
    Returns:
        Result dictionary with success status
        
    Raises:
        ValueError: If policy not found
    """
    policies_data = load_policies(storage_root, use_cache=False)
    
    original_count = len(policies_data.get("policies", []))
    policies_data["policies"] = [
        p for p in policies_data.get("policies", [])
        if p.get("id") != policy_id
    ]
    
    if len(policies_data["policies"]) == original_count:
        raise ValueError(f"Policy '{policy_id}' not found")
    
    if save_policies(storage_root, policies_data):
        return {"success": True, "message": f"Policy '{policy_id}' deleted"}
    else:
        raise IOError("Failed to save policies after deletion")


def clear_policy_cache() -> None:
    """Clear the policy cache to force reload on next access."""
    _policy_cache.clear()
    logger.info("Policy cache cleared")


def get_policy_by_id(storage_root: str, policy_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single policy by its ID.
    
    Args:
        storage_root: Path to the data storage directory
        policy_id: The policy ID (e.g., "CVD-BP-001")
        
    Returns:
        The policy dictionary or None if not found
    """
    policies = load_policies(storage_root)
    
    for policy in policies.get("policies", []):
        if policy.get("id") == policy_id:
            return policy
    
    return None


def get_policies_by_category(storage_root: str, category: str) -> List[Dict[str, Any]]:
    """
    Get all policies in a specific category.
    
    Args:
        storage_root: Path to the data storage directory
        category: The category name (e.g., "cardiovascular", "metabolic")
        
    Returns:
        List of policies in the category
    """
    policies = load_policies(storage_root)
    
    return [
        policy for policy in policies.get("policies", [])
        if policy.get("category", "").lower() == category.lower()
    ]


def get_policies_for_conditions(
    storage_root: str,
    conditions: List[str]
) -> List[Dict[str, Any]]:
    """
    Get relevant policies based on extracted medical conditions.
    
    This function maps common condition keywords to relevant policies.
    
    Args:
        storage_root: Path to the data storage directory
        conditions: List of condition strings extracted from application
        
    Returns:
        List of relevant policies
    """
    policies = load_policies(storage_root)
    all_policies = policies.get("policies", [])
    
    # Keyword to policy ID mapping
    keyword_mapping = {
        # Cardiovascular
        "hypertension": ["CVD-BP-001"],
        "high blood pressure": ["CVD-BP-001"],
        "blood pressure": ["CVD-BP-001"],
        "bp": ["CVD-BP-001"],
        
        # Cholesterol
        "cholesterol": ["META-CHOL-001"],
        "lipid": ["META-CHOL-001"],
        "dyslipidemia": ["META-CHOL-001"],
        "hyperlipidemia": ["META-CHOL-001"],
        "ldl": ["META-CHOL-001"],
        "hdl": ["META-CHOL-001"],
        "triglycerides": ["META-CHOL-001"],
        
        # Diabetes
        "diabetes": ["META-DM-001"],
        "diabetic": ["META-DM-001"],
        "glucose": ["META-DM-001"],
        "hba1c": ["META-DM-001"],
        "a1c": ["META-DM-001"],
        "blood sugar": ["META-DM-001"],
        
        # BMI
        "bmi": ["META-BMI-001"],
        "obesity": ["META-BMI-001"],
        "obese": ["META-BMI-001"],
        "overweight": ["META-BMI-001"],
        "underweight": ["META-BMI-001"],
        "weight": ["META-BMI-001"],
        
        # Thyroid
        "thyroid": ["ENDO-THY-001"],
        "hypothyroid": ["ENDO-THY-001"],
        "hyperthyroid": ["ENDO-THY-001"],
        "tsh": ["ENDO-THY-001"],
        "graves": ["ENDO-THY-001"],
        "hashimoto": ["ENDO-THY-001"],
        
        # Family history
        "family history": ["FAM-CVD-001", "FAM-CA-001"],
        "heart disease": ["FAM-CVD-001", "CVD-BP-001"],
        "cardiovascular": ["FAM-CVD-001", "CVD-BP-001"],
        "cancer": ["FAM-CA-001"],
        "brca": ["FAM-CA-001"],
        "lynch": ["FAM-CA-001"],
        
        # Lifestyle
        "smoking": ["LIFE-TOB-001"],
        "smoker": ["LIFE-TOB-001"],
        "tobacco": ["LIFE-TOB-001"],
        "nicotine": ["LIFE-TOB-001"],
        "vaping": ["LIFE-TOB-001"],
        "alcohol": ["LIFE-ALC-001"],
        "drinking": ["LIFE-ALC-001"],
        "dui": ["LIFE-ALC-001"],
        
        # Occupation
        "occupation": ["LIFE-OCC-001"],
        "pilot": ["LIFE-OCC-001"],
        "military": ["LIFE-OCC-001"],
        "firefighter": ["LIFE-OCC-001"],
        "police": ["LIFE-OCC-001"],
        "mining": ["LIFE-OCC-001"],
        "construction": ["LIFE-OCC-001"],
    }
    
    matched_policy_ids = set()
    
    # Search for keyword matches in conditions
    conditions_lower = " ".join(conditions).lower()
    
    for keyword, policy_ids in keyword_mapping.items():
        if keyword in conditions_lower:
            matched_policy_ids.update(policy_ids)
    
    # Get the actual policy objects
    matched_policies = [
        policy for policy in all_policies
        if policy.get("id") in matched_policy_ids
    ]
    
    logger.info(
        "Matched %d policies for conditions: %s",
        len(matched_policies),
        matched_policy_ids
    )
    
    return matched_policies


def get_all_policy_ids(storage_root: str) -> List[str]:
    """Get a list of all policy IDs."""
    policies = load_policies(storage_root)
    return [policy.get("id") for policy in policies.get("policies", [])]


def format_policy_for_prompt(policy: Dict[str, Any]) -> str:
    """
    Format a single policy for injection into an LLM prompt.
    
    Args:
        policy: The policy dictionary
        
    Returns:
        Formatted string representation of the policy
    """
    lines = []
    lines.append(f"### Policy: {policy['id']} - {policy['name']}")
    lines.append(f"Category: {policy['category']}/{policy['subcategory']}")
    lines.append(f"Description: {policy['description']}")
    lines.append("")
    lines.append("**Risk Assessment Criteria:**")
    
    for criteria in policy.get("criteria", []):
        lines.append(f"- [{criteria['id']}] {criteria['condition']}")
        lines.append(f"  - Risk Level: {criteria['risk_level']}")
        lines.append(f"  - Action: {criteria['action']}")
        lines.append(f"  - Rationale: {criteria['rationale']}")
    
    if policy.get("modifying_factors"):
        lines.append("")
        lines.append("**Modifying Factors:**")
        for factor in policy["modifying_factors"]:
            lines.append(f"- {factor['factor']}: {factor['impact']}")
    
    return "\n".join(lines)


def format_policies_for_prompt(
    policies: List[Dict[str, Any]],
    max_policies: int = 10
) -> str:
    """
    Format multiple policies for injection into an LLM prompt.
    
    Args:
        policies: List of policy dictionaries
        max_policies: Maximum number of policies to include
        
    Returns:
        Formatted string containing all policies
    """
    if not policies:
        return "No specific underwriting policies applicable."
    
    # Limit policies to avoid token overflow
    policies_to_format = policies[:max_policies]
    
    lines = [
        "# UNDERWRITING POLICY REFERENCE",
        "",
        "Use the following underwriting policies to assess risk and determine appropriate actions.",
        "When providing a risk assessment, you MUST cite the specific policy and criteria used.",
        "",
    ]
    
    for policy in policies_to_format:
        lines.append(format_policy_for_prompt(policy))
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("## Citation Requirements")
    lines.append("")
    lines.append("For each risk assessment, provide policy_citations with:")
    lines.append("- policy_id: The policy ID (e.g., CVD-BP-001)")
    lines.append("- criteria_id: The specific criteria ID matched (e.g., CVD-BP-001-C)")
    lines.append("- policy_name: The policy name")
    lines.append("- matched_condition: The condition text that was matched")
    lines.append("- applied_action: The recommended action from the policy")
    lines.append("- rationale: The policy rationale for this determination")
    
    return "\n".join(lines)


def format_all_policies_for_prompt(storage_root: str) -> str:
    """
    Format all policies for injection into a prompt.
    
    Args:
        storage_root: Path to the data storage directory
        
    Returns:
        Formatted string containing all policies
    """
    policies = load_policies(storage_root)
    return format_policies_for_prompt(policies.get("policies", []))


def format_relevant_policies_for_prompt(
    storage_root: str,
    document_text: str,
    max_policies: int = 6
) -> str:
    """
    Format only relevant policies based on document content.
    
    This function analyzes the document text to identify relevant conditions
    and returns only the policies that apply.
    
    Args:
        storage_root: Path to the data storage directory
        document_text: The application/document text to analyze
        max_policies: Maximum number of policies to include
        
    Returns:
        Formatted string containing relevant policies
    """
    # Extract potential conditions from document
    conditions = [document_text]  # Simple approach - search whole text
    
    relevant_policies = get_policies_for_conditions(storage_root, conditions)
    
    # If no specific matches, include core policies
    if not relevant_policies:
        all_policies = load_policies(storage_root).get("policies", [])
        # Default to first few policies as baseline
        relevant_policies = all_policies[:max_policies]
    
    return format_policies_for_prompt(relevant_policies, max_policies)


def validate_policy_citation(
    storage_root: str,
    policy_id: str,
    criteria_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate that a policy citation is valid.
    
    Args:
        storage_root: Path to the data storage directory
        policy_id: The policy ID to validate
        criteria_id: Optional criteria ID to validate
        
    Returns:
        Dictionary with validation result and policy details
    """
    policy = get_policy_by_id(storage_root, policy_id)
    
    if not policy:
        return {
            "valid": False,
            "error": f"Policy {policy_id} not found",
            "policy": None,
            "criteria": None,
        }
    
    if criteria_id:
        criteria = None
        for c in policy.get("criteria", []):
            if c.get("id") == criteria_id:
                criteria = c
                break
        
        if not criteria:
            return {
                "valid": False,
                "error": f"Criteria {criteria_id} not found in policy {policy_id}",
                "policy": policy,
                "criteria": None,
            }
        
        return {
            "valid": True,
            "error": None,
            "policy": policy,
            "criteria": criteria,
        }
    
    return {
        "valid": True,
        "error": None,
        "policy": policy,
        "criteria": None,
    }


# Mapping of personas to their policy JSON files
PERSONA_POLICY_FILES = {
    "underwriting": "life-health-underwriting-policies.json",
    "life_health_claims": "life-health-claims-policies.json",
    "automotive_claims": "automotive-claims-policies.json",
    "property_casualty_claims": "property-casualty-claims-policies.json",
}


def get_policy_file_for_persona(storage_root: str, persona: str) -> str:
    """
    Get the path to the policy file for a specific persona.
    
    Args:
        storage_root: Path to the data storage directory
        persona: Persona type (underwriting, life_health_claims, etc.)
        
    Returns:
        Path to the persona's policy JSON file
    """
    policy_file = PERSONA_POLICY_FILES.get(persona, PERSONA_POLICY_FILES["underwriting"])
    return os.path.join(storage_root, policy_file)


def load_policies_for_persona(
    storage_root: str,
    persona: str,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Load policies from the JSON file for a specific persona.
    
    Args:
        storage_root: Path to the data storage directory
        persona: Persona type (underwriting, life_health_claims, etc.)
        use_cache: Whether to use cached policies if available
        
    Returns:
        Dictionary containing the full policies structure
    """
    cache_key = f"{storage_root}:{persona}"
    
    if use_cache and cache_key in _policy_cache:
        return _policy_cache[cache_key]
    
    policy_file = get_policy_file_for_persona(storage_root, persona)
    
    try:
        if os.path.exists(policy_file):
            with open(policy_file, 'r', encoding='utf-8') as f:
                policies = json.load(f)
                
            # Validate basic structure
            if "policies" not in policies or not isinstance(policies["policies"], list):
                logger.warning(f"Invalid policy file structure for {persona}. Expected 'policies' array.")
                return _get_empty_policies()
            
            logger.info(
                "Loaded %d %s policies from %s",
                len(policies["policies"]),
                persona,
                policy_file
            )
            
            if use_cache:
                _policy_cache[cache_key] = policies
                
            return policies
        else:
            logger.warning("Policy file not found for %s: %s", persona, policy_file)
            return _get_empty_policies()
            
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load %s policies: %s", persona, str(e))
        return _get_empty_policies()


def format_policies_for_persona(storage_root: str, persona: str) -> str:
    """
    Format all policies for a specific persona for injection into a prompt.
    
    This is the persona-aware version of format_all_policies_for_prompt.
    
    Args:
        storage_root: Path to the data storage directory
        persona: Persona type (underwriting, life_health_claims, etc.)
        
    Returns:
        Formatted string containing all policies for the persona
    """
    policies = load_policies_for_persona(storage_root, persona)
    return format_policies_for_prompt(policies.get("policies", []))
