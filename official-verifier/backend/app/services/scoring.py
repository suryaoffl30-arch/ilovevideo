"""Scoring engine for entity confidence calculation."""
from typing import List, Dict, Tuple
from uuid import UUID

# Signal presets: (score_contribution, weight)
SIGNAL_PRESETS = {
    'wikipedia': (45.0, 1.5),
    'appstore': (50.0, 1.5),
    'playstore': (50.0, 1.5),
    'gov_registry': (60.0, 2.0),
    'whois_age_long': (15.0, 1.0),
    'ssl_cn_match': (15.0, 1.1),
    'backlinks_reputable': (20.0, 1.0),
    'new_domain_penalty': (-30.0, 1.0),
    'homoglyph_penalty': (-40.0, 1.0),
    'registrar_penalty': (-20.0, 1.0),
}


def calculate_risk_level(score: float) -> str:
    """
    Calculate risk level from confidence score.
    
    Args:
        score: Confidence score (0-100)
    
    Returns:
        Risk level: 'none', 'low', 'medium', or 'high'
    """
    if score >= 90:
        return 'none'
    elif score >= 60:
        return 'low'
    elif score >= 30:
        return 'medium'
    else:
        return 'high'


def compute_score(verifications: List[Dict], lookalikes: List[Dict]) -> Tuple[float, str]:
    """
    Compute entity confidence score from verifications and lookalikes.
    
    Args:
        verifications: List of verification records with score_contrib, weight, expires_at
        lookalikes: List of lookalike domains with distance and flagged status
    
    Returns:
        Tuple of (score, risk_level)
    """
    import datetime
    
    score_sum = 0.0
    
    # Sum verification contributions
    for v in verifications:
        if v.get('status') not in ['verified', 'needs_review']:
            continue
        
        contrib = float(v['score_contrib']) * float(v['weight'])
        
        # Apply expiration multiplier
        if v.get('expires_at'):
            if isinstance(v['expires_at'], str):
                expires_at = datetime.datetime.fromisoformat(v['expires_at'].replace('Z', '+00:00'))
            else:
                expires_at = v['expires_at']
            
            if expires_at < datetime.datetime.now(datetime.timezone.utc):
                contrib *= 0.5
        
        score_sum += contrib
    
    # Apply lookalike penalty
    for lookalike in lookalikes:
        if lookalike.get('flagged') and lookalike.get('distance', 999) < 2:
            score_sum -= 40
            break  # Only apply penalty once
    
    # Cap score
    final_score = max(0, min(100, score_sum))
    risk_level = calculate_risk_level(final_score)
    
    return round(final_score, 2), risk_level


def explain_score(verifications: List[Dict], lookalikes: List[Dict]) -> List[Dict]:
    """
    Explain score calculation with breakdown of contributions.
    
    Args:
        verifications: List of verification records
        lookalikes: List of lookalike domains
    
    Returns:
        List of contribution explanations
    """
    import datetime
    
    explanations = []
    
    for v in verifications:
        if v.get('status') not in ['verified', 'needs_review']:
            continue
        
        contrib = v['score_contrib'] * v['weight']
        multiplier = 1.0
        note = ""
        
        if v.get('expires_at'):
            if isinstance(v['expires_at'], str):
                expires_at = datetime.datetime.fromisoformat(v['expires_at'].replace('Z', '+00:00'))
            else:
                expires_at = v['expires_at']
            
            if expires_at < datetime.datetime.now(datetime.timezone.utc):
                multiplier = 0.5
                note = " (expired, 50% weight)"
        
        explanations.append({
            'source_type': v.get('source_type', 'unknown'),
            'base_score': v['score_contrib'],
            'weight': v['weight'],
            'contribution': round(contrib * multiplier, 2),
            'note': note
        })
    
    # Lookalike penalties
    for lookalike in lookalikes:
        if lookalike.get('flagged') and lookalike.get('distance', 999) < 2:
            explanations.append({
                'source_type': 'lookalike_penalty',
                'base_score': -40,
                'weight': 1.0,
                'contribution': -40,
                'note': f" (similar domain: {lookalike.get('domain')})"
            })
            break
    
    return explanations
