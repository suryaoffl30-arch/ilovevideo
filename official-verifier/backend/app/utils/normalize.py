"""Utility functions for normalization and detection."""
import re
from typing import Optional
from urllib.parse import urlparse


def normalize_name(name: str) -> str:
    """
    Normalize entity name for comparison.
    
    Args:
        name: Entity name
    
    Returns:
        Normalized name (lowercase, stripped)
    """
    return name.lower().strip()


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
    
    Returns:
        Domain without www prefix
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except Exception:
        return None


def is_homoglyph_like(domain: str, entity_name: str) -> bool:
    """
    Check if domain contains homoglyphs similar to entity name.
    
    This is a simple implementation. For production, consider using
    a dedicated homoglyph detection library.
    
    Args:
        domain: Domain to check
        entity_name: Entity name to compare against
    
    Returns:
        True if potential homoglyph detected
    """
    # Common homoglyphs
    homoglyphs = {
        'a': ['а', 'ɑ', 'α'],  # Cyrillic a, Latin alpha, Greek alpha
        'e': ['е', 'ε'],        # Cyrillic e, Greek epsilon
        'o': ['о', 'ο', '0'],   # Cyrillic o, Greek omicron, zero
        'p': ['р', 'ρ'],        # Cyrillic r, Greek rho
        'c': ['с', 'ϲ'],        # Cyrillic s, Greek lunate sigma
        'i': ['і', 'ι', '1'],   # Cyrillic i, Greek iota, one
        'l': ['ӏ', '1', 'ǀ'],   # Cyrillic palochka, one, Latin letter alveolar click
    }
    
    # Normalize entity name for comparison
    normalized_entity = normalize_name(entity_name).replace(' ', '')
    domain_lower = domain.lower()
    
    # Check if domain contains entity name with potential homoglyphs
    for char in normalized_entity:
        if char in homoglyphs:
            for homoglyph in homoglyphs[char]:
                if homoglyph in domain_lower:
                    return True
    
    return False


def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        Edit distance
    """
    if len(s1) < len(s2):
        return calculate_levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def is_typosquatting(domain: str, official_domain: str, threshold: int = 2) -> bool:
    """
    Check if domain is potential typosquatting of official domain.
    
    Args:
        domain: Domain to check
        official_domain: Official domain
        threshold: Maximum edit distance to consider typosquatting
    
    Returns:
        True if potential typosquatting detected
    """
    distance = calculate_levenshtein_distance(domain, official_domain)
    return distance <= threshold and distance > 0
