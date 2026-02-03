"""
Glossary management for WorkbenchIQ.

Handles loading, saving, and CRUD operations for persona-specific glossaries.
Each persona has its own glossary with categories and terms.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Default glossary file path
GLOSSARY_FILENAME = "glossary.json"


def _get_glossary_file_path(prompts_root: str) -> Path:
    """Get the path to the glossary file."""
    return Path(prompts_root) / GLOSSARY_FILENAME


def load_glossary(prompts_root: str) -> Dict[str, Any]:
    """
    Load the entire glossary file.
    
    Args:
        prompts_root: Path to the prompts directory
        
    Returns:
        Dictionary containing the full glossary data
        
    Raises:
        FileNotFoundError: If glossary file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    glossary_path = _get_glossary_file_path(prompts_root)
    
    if not glossary_path.exists():
        logger.warning("Glossary file not found: %s", glossary_path)
        return {"version": "1.0", "personas": {}}
    
    with open(glossary_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_glossary(prompts_root: str, glossary: Dict[str, Any]) -> None:
    """
    Save the glossary to file.
    
    Args:
        prompts_root: Path to the prompts directory
        glossary: Full glossary dictionary to save
    """
    glossary_path = _get_glossary_file_path(prompts_root)
    
    with open(glossary_path, 'w', encoding='utf-8') as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)
    
    logger.info("Saved glossary to %s", glossary_path)


def get_glossary_for_persona(prompts_root: str, persona: str) -> Dict[str, Any]:
    """
    Get glossary entries for a specific persona.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona ID (e.g., 'underwriting', 'mortgage')
        
    Returns:
        Dictionary with persona glossary data including categories and terms
        
    Raises:
        ValueError: If persona not found in glossary
    """
    glossary = load_glossary(prompts_root)
    personas = glossary.get("personas", {})
    
    # Handle persona aliases
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in personas:
        raise ValueError(f"Persona '{persona}' not found in glossary")
    
    persona_data = personas[persona_key]
    
    # Count total terms
    total_terms = sum(
        len(category.get("terms", []))
        for category in persona_data.get("categories", [])
    )
    
    return {
        "persona": persona_key,
        "name": persona_data.get("name", persona_key),
        "description": persona_data.get("description", ""),
        "categories": persona_data.get("categories", []),
        "total_terms": total_terms
    }


def _resolve_persona_alias(persona: str) -> str:
    """Resolve persona aliases to canonical names."""
    aliases = {
        "mortgage_underwriting": "mortgage",
        "claims": "life_health_claims",
        "property_casualty_claims": "automotive_claims",
    }
    return aliases.get(persona, persona)


def list_glossaries(prompts_root: str) -> List[Dict[str, Any]]:
    """
    List all available glossaries with summary info.
    
    Args:
        prompts_root: Path to the prompts directory
        
    Returns:
        List of glossary summaries
    """
    glossary = load_glossary(prompts_root)
    personas = glossary.get("personas", {})
    
    result = []
    for persona_id, persona_data in personas.items():
        categories = persona_data.get("categories", [])
        total_terms = sum(len(c.get("terms", [])) for c in categories)
        
        result.append({
            "persona": persona_id,
            "name": persona_data.get("name", persona_id),
            "description": persona_data.get("description", ""),
            "term_count": total_terms,
            "category_count": len(categories)
        })
    
    return result


def search_glossary(
    prompts_root: str,
    persona: str,
    query: str,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for terms matching a query.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona to search within
        query: Search query (matches abbreviation or meaning)
        category: Optional category ID to filter by
        
    Returns:
        List of matching terms with category info
    """
    try:
        persona_glossary = get_glossary_for_persona(prompts_root, persona)
    except ValueError:
        return []
    
    query_lower = query.lower()
    results = []
    
    for cat in persona_glossary.get("categories", []):
        cat_id = cat.get("id", "")
        cat_name = cat.get("name", "")
        
        # Skip if category filter specified and doesn't match
        if category and cat_id != category:
            continue
        
        for term in cat.get("terms", []):
            abbreviation = term.get("abbreviation", "")
            meaning = term.get("meaning", "")
            context = term.get("context", "")
            
            # Check if query matches abbreviation or meaning
            if (query_lower in abbreviation.lower() or 
                query_lower in meaning.lower() or
                query_lower in context.lower()):
                results.append({
                    "abbreviation": abbreviation,
                    "meaning": meaning,
                    "context": context,
                    "examples": term.get("examples", []),
                    "category": cat_name,
                    "category_id": cat_id
                })
    
    # Sort by abbreviation
    results.sort(key=lambda x: x["abbreviation"].lower())
    
    return results


def add_term(
    prompts_root: str,
    persona: str,
    category_id: str,
    term: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a new term to a persona's glossary.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona to add term to
        category_id: The category ID to add term to
        term: Term data with abbreviation, meaning, etc.
        
    Returns:
        The added term
        
    Raises:
        ValueError: If persona, category not found, or term already exists
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    categories = persona_data.get("categories", [])
    
    # Find the category
    category = None
    for cat in categories:
        if cat.get("id") == category_id:
            category = cat
            break
    
    if category is None:
        raise ValueError(f"Category '{category_id}' not found in persona '{persona}'")
    
    # Check for duplicate abbreviation
    abbreviation = term.get("abbreviation", "")
    for existing_cat in categories:
        for existing_term in existing_cat.get("terms", []):
            if existing_term.get("abbreviation", "").lower() == abbreviation.lower():
                raise ValueError(f"Term '{abbreviation}' already exists in persona '{persona}'")
    
    # Add the term
    new_term = {
        "abbreviation": abbreviation,
        "meaning": term.get("meaning", ""),
    }
    if term.get("context"):
        new_term["context"] = term["context"]
    if term.get("examples"):
        new_term["examples"] = term["examples"]
    
    if "terms" not in category:
        category["terms"] = []
    category["terms"].append(new_term)
    
    # Sort terms alphabetically
    category["terms"].sort(key=lambda x: x["abbreviation"].lower())
    
    # Save
    save_glossary(prompts_root, glossary)
    
    return new_term


def update_term(
    prompts_root: str,
    persona: str,
    abbreviation: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing term.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona containing the term
        abbreviation: The abbreviation to update
        updates: Dictionary of fields to update
        
    Returns:
        The updated term
        
    Raises:
        ValueError: If term not found
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    categories = persona_data.get("categories", [])
    
    # Find the term
    found_term = None
    found_category = None
    found_category_idx = None
    found_term_idx = None
    
    for cat_idx, cat in enumerate(categories):
        for term_idx, term in enumerate(cat.get("terms", [])):
            if term.get("abbreviation", "").lower() == abbreviation.lower():
                found_term = term
                found_category = cat
                found_category_idx = cat_idx
                found_term_idx = term_idx
                break
        if found_term:
            break
    
    if not found_term:
        raise ValueError(f"Term '{abbreviation}' not found in persona '{persona}'")
    
    # Handle category change
    new_category_id = updates.get("category_id")
    if new_category_id and new_category_id != found_category.get("id"):
        # Find new category
        new_category = None
        for cat in categories:
            if cat.get("id") == new_category_id:
                new_category = cat
                break
        
        if not new_category:
            raise ValueError(f"Category '{new_category_id}' not found")
        
        # Remove from old category
        found_category["terms"].pop(found_term_idx)
        
        # Add to new category
        if "terms" not in new_category:
            new_category["terms"] = []
        new_category["terms"].append(found_term)
        new_category["terms"].sort(key=lambda x: x["abbreviation"].lower())
    
    # Update fields
    if "meaning" in updates:
        found_term["meaning"] = updates["meaning"]
    if "context" in updates:
        found_term["context"] = updates["context"]
    if "examples" in updates:
        found_term["examples"] = updates["examples"]
    
    # Save
    save_glossary(prompts_root, glossary)
    
    return found_term


def delete_term(prompts_root: str, persona: str, abbreviation: str) -> bool:
    """
    Delete a term from the glossary.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona containing the term
        abbreviation: The abbreviation to delete
        
    Returns:
        True if deleted
        
    Raises:
        ValueError: If term not found
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    categories = persona_data.get("categories", [])
    
    # Find and delete the term
    for cat in categories:
        terms = cat.get("terms", [])
        for idx, term in enumerate(terms):
            if term.get("abbreviation", "").lower() == abbreviation.lower():
                terms.pop(idx)
                save_glossary(prompts_root, glossary)
                return True
    
    raise ValueError(f"Term '{abbreviation}' not found in persona '{persona}'")


def add_category(
    prompts_root: str,
    persona: str,
    category: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a new category to a persona's glossary.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona to add category to
        category: Category data with id and name
        
    Returns:
        The added category
        
    Raises:
        ValueError: If category already exists
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    
    if "categories" not in persona_data:
        persona_data["categories"] = []
    
    categories = persona_data["categories"]
    
    # Check for duplicate
    category_id = category.get("id", "")
    for existing in categories:
        if existing.get("id") == category_id:
            raise ValueError(f"Category '{category_id}' already exists in persona '{persona}'")
    
    # Add new category
    new_category = {
        "id": category_id,
        "name": category.get("name", category_id),
        "terms": []
    }
    categories.append(new_category)
    
    # Sort categories by name
    categories.sort(key=lambda x: x.get("name", "").lower())
    
    save_glossary(prompts_root, glossary)
    
    return new_category


def update_category(
    prompts_root: str,
    persona: str,
    category_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing category.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona containing the category
        category_id: The category ID to update
        updates: Dictionary of fields to update (name only)
        
    Returns:
        The updated category
        
    Raises:
        ValueError: If category not found
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    categories = persona_data.get("categories", [])
    
    # Find the category
    for cat in categories:
        if cat.get("id") == category_id:
            if "name" in updates:
                cat["name"] = updates["name"]
            save_glossary(prompts_root, glossary)
            return cat
    
    raise ValueError(f"Category '{category_id}' not found in persona '{persona}'")


def delete_category(prompts_root: str, persona: str, category_id: str) -> bool:
    """
    Delete a category (must be empty).
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona containing the category
        category_id: The category ID to delete
        
    Returns:
        True if deleted
        
    Raises:
        ValueError: If category not found or not empty
    """
    glossary = load_glossary(prompts_root)
    persona_key = _resolve_persona_alias(persona)
    
    if persona_key not in glossary.get("personas", {}):
        raise ValueError(f"Persona '{persona}' not found")
    
    persona_data = glossary["personas"][persona_key]
    categories = persona_data.get("categories", [])
    
    # Find and delete the category
    for idx, cat in enumerate(categories):
        if cat.get("id") == category_id:
            if cat.get("terms") and len(cat["terms"]) > 0:
                raise ValueError(f"Category '{category_id}' is not empty. Delete all terms first.")
            categories.pop(idx)
            save_glossary(prompts_root, glossary)
            return True
    
    raise ValueError(f"Category '{category_id}' not found in persona '{persona}'")


def format_glossary_for_prompt(
    prompts_root: str,
    persona: str,
    max_terms: int = 100,
    categories: Optional[List[str]] = None,
    format_type: str = "markdown",
    include_category_headers: bool = False
) -> str:
    """
    Format glossary as a string suitable for LLM prompt injection.
    
    Args:
        prompts_root: Path to the prompts directory
        persona: The persona to get glossary for
        max_terms: Maximum terms to include
        categories: Optional list of category IDs to include
        format_type: Output format - "markdown" (table) or "list"
        include_category_headers: Whether to include category section headers
        
    Returns:
        Formatted string ready for prompt injection
    """
    try:
        persona_glossary = get_glossary_for_persona(prompts_root, persona)
    except ValueError:
        logger.warning("No glossary found for persona: %s", persona)
        return ""
    except Exception as e:
        logger.warning("Error loading glossary for %s: %s", persona, e)
        return ""
    
    all_terms = []
    
    for cat in persona_glossary.get("categories", []):
        cat_id = cat.get("id", "")
        cat_name = cat.get("name", "")
        
        # Skip if category filter specified and doesn't match
        if categories and cat_id not in categories:
            continue
        
        for term in cat.get("terms", []):
            all_terms.append({
                "abbreviation": term.get("abbreviation", ""),
                "meaning": term.get("meaning", ""),
                "category": cat_name
            })
    
    # Limit terms
    if len(all_terms) > max_terms:
        all_terms = all_terms[:max_terms]
    
    if not all_terms:
        return ""
    
    # Format output
    if format_type == "markdown":
        return _format_as_markdown(all_terms, include_category_headers)
    else:
        return _format_as_list(all_terms, include_category_headers)


def _format_as_markdown(terms: List[Dict], include_headers: bool) -> str:
    """Format terms as markdown table."""
    lines = ["## Domain Terminology Reference", ""]
    
    if include_headers:
        # Group by category
        by_category = {}
        for term in terms:
            cat = term.get("category", "Other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(term)
        
        for cat_name, cat_terms in sorted(by_category.items()):
            lines.append(f"### {cat_name}")
            lines.append("")
            lines.append("| Abbreviation | Meaning |")
            lines.append("|-------------|---------|")
            for term in cat_terms:
                lines.append(f"| {term['abbreviation']} | {term['meaning']} |")
            lines.append("")
    else:
        lines.append("| Abbreviation | Meaning |")
        lines.append("|-------------|---------|")
        for term in sorted(terms, key=lambda x: x["abbreviation"].lower()):
            lines.append(f"| {term['abbreviation']} | {term['meaning']} |")
    
    return "\n".join(lines)


def _format_as_list(terms: List[Dict], include_headers: bool) -> str:
    """Format terms as simple list."""
    lines = ["Domain Terminology:", ""]
    
    if include_headers:
        by_category = {}
        for term in terms:
            cat = term.get("category", "Other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(term)
        
        for cat_name, cat_terms in sorted(by_category.items()):
            lines.append(f"{cat_name}:")
            for term in cat_terms:
                lines.append(f"  - {term['abbreviation']}: {term['meaning']}")
            lines.append("")
    else:
        for term in sorted(terms, key=lambda x: x["abbreviation"].lower()):
            lines.append(f"- {term['abbreviation']}: {term['meaning']}")
    
    return "\n".join(lines)
