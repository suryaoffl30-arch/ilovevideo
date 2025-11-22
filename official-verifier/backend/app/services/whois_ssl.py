"""WHOIS and SSL verification stubs.

TODO: Implement full WHOIS and SSL certificate verification.
For production, consider using:
- python-whois library for WHOIS lookups
- ssl and socket modules for certificate verification
- Third-party APIs like WhoisXML API or SecurityTrails
"""
from typing import Optional, Dict
from datetime import datetime, timedelta


async def check_whois_age(domain: str) -> Optional[Dict]:
    """
    Check domain age via WHOIS (stub implementation).
    
    Args:
        domain: Domain name to check
    
    Returns:
        Dictionary with whois data or None
    
    TODO: Implement actual WHOIS lookup using python-whois or API
    """
    # Stub implementation
    # In production, use: import whois; w = whois.whois(domain)
    return {
        'domain': domain,
        'creation_date': datetime.now() - timedelta(days=365 * 5),  # Stub: 5 years old
        'registrar': 'Example Registrar',
        'age_days': 365 * 5
    }


async def check_ssl_certificate(domain: str) -> Optional[Dict]:
    """
    Check SSL certificate and CN match (stub implementation).
    
    Args:
        domain: Domain name to check
    
    Returns:
        Dictionary with SSL data or None
    
    TODO: Implement actual SSL certificate verification
    """
    # Stub implementation
    # In production, use ssl.get_server_certificate() and parse cert
    return {
        'domain': domain,
        'has_ssl': True,
        'cn_match': True,
        'issuer': 'Example CA',
        'valid_until': datetime.now() + timedelta(days=90)
    }


async def verify_domain_signals(domain: str) -> Dict:
    """
    Verify domain using WHOIS and SSL checks.
    
    Args:
        domain: Domain to verify
    
    Returns:
        Dictionary with verification signals
    """
    whois_data = await check_whois_age(domain)
    ssl_data = await check_ssl_certificate(domain)
    
    signals = {}
    
    # WHOIS age signal
    if whois_data and whois_data.get('age_days', 0) > 365:
        signals['whois_age_long'] = {
            'score_contrib': 15.0,
            'weight': 1.0,
            'evidence': {'age_days': whois_data['age_days']}
        }
    elif whois_data and whois_data.get('age_days', 0) < 90:
        signals['new_domain_penalty'] = {
            'score_contrib': -30.0,
            'weight': 1.0,
            'evidence': {'age_days': whois_data['age_days']}
        }
    
    # SSL CN match signal
    if ssl_data and ssl_data.get('cn_match'):
        signals['ssl_cn_match'] = {
            'score_contrib': 15.0,
            'weight': 1.1,
            'evidence': {'issuer': ssl_data.get('issuer')}
        }
    
    return signals
